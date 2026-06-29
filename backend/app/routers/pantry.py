"""Endpoints de despensa (§6): GET/POST/DELETE /pantry — pantalla "Mi despensa" (§8).

Todo se hace sobre el hogar del usuario autenticado.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.hogar import Hogar
from app.models.item_despensa import ItemDespensa
from app.models.usuario import RolUsuario, Usuario
from app.routers.hogar import hogar_de_usuario
from app.schemas.pantry import ItemDespensaCreate, ItemDespensaOut
from app.schemas.plan import ScanResultado
from app.services import ocr

router = APIRouter(
    tags=["pantry"],
    dependencies=[Depends(require_rol(RolUsuario.cliente, RolUsuario.admin))],
)


def _hogar_obligatorio(db: Session, current: Usuario) -> Hogar:
    hogar = hogar_de_usuario(db, current.id)
    if hogar is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Crea tu hogar (onboarding) antes de usar la despensa.",
        )
    return hogar


@router.get("/pantry", response_model=list[ItemDespensaOut], summary="Listar despensa")
def listar(
    db: Session = Depends(get_db), current: Usuario = Depends(get_current_user)
) -> list[ItemDespensa]:
    hogar = _hogar_obligatorio(db, current)
    # Ordena por proximidad de caducidad (sin fecha al final) — apoya "úsalo primero".
    return list(
        db.scalars(
            select(ItemDespensa)
            .where(ItemDespensa.hogar_id == hogar.id)
            .order_by(
                ItemDespensa.fecha_caducidad.is_(None),
                ItemDespensa.fecha_caducidad.asc(),
            )
        ).all()
    )


@router.post(
    "/pantry",
    response_model=ItemDespensaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar item a la despensa",
)
def agregar(
    data: ItemDespensaCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> ItemDespensa:
    hogar = _hogar_obligatorio(db, current)
    item = ItemDespensa(hogar_id=hogar.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post(
    "/pantry/scan-ticket",
    response_model=ScanResultado,
    summary="OCR de ticket → agrega items a la despensa",
)
async def scan_ticket(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> ScanResultado:
    hogar = _hogar_obligatorio(db, current)
    contenido = await file.read()
    if not contenido:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La imagen está vacía.")
    try:
        items, texto = ocr.escanear_ticket(contenido)
    except ocr.OCRNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))

    existentes = {
        i.nombre.strip().lower()
        for i in db.scalars(
            select(ItemDespensa).where(ItemDespensa.hogar_id == hogar.id)
        ).all()
    }
    agregados = 0
    for nombre in items:
        clave = nombre.lower()
        if clave not in existentes:
            db.add(ItemDespensa(hogar_id=hogar.id, nombre=nombre[:120]))
            existentes.add(clave)
            agregados += 1
    db.commit()
    return ScanResultado(items=items, agregados=agregados, texto_ocr=(texto or "")[:2000])


@router.delete(
    "/pantry/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar item de la despensa",
)
def borrar(
    item_id: int,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> None:
    hogar = _hogar_obligatorio(db, current)
    item = db.get(ItemDespensa, item_id)
    if item is None or item.hogar_id != hogar.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item no encontrado")
    db.delete(item)
    db.commit()

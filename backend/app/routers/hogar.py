"""Endpoint del hogar — soporta el onboarding (§8).

MVP: un hogar por usuario. POST /hogar hace upsert (crea o actualiza).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.hogar import Hogar
from app.models.usuario import RolUsuario, Usuario
from app.schemas.hogar import HogarCreate, HogarOut

router = APIRouter(
    tags=["hogar"],
    dependencies=[Depends(require_rol(RolUsuario.cliente, RolUsuario.admin))],
)


def hogar_de_usuario(db: Session, usuario_id: int) -> Hogar | None:
    return db.scalar(select(Hogar).where(Hogar.usuario_id == usuario_id))


@router.get("/hogar", response_model=HogarOut, summary="Mi hogar")
def mi_hogar(
    db: Session = Depends(get_db), current: Usuario = Depends(get_current_user)
) -> Hogar:
    hogar = hogar_de_usuario(db, current.id)
    if hogar is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aún no has creado tu hogar")
    return hogar


@router.post("/hogar", response_model=HogarOut, summary="Crear/actualizar mi hogar (onboarding)")
def crear_o_actualizar_hogar(
    data: HogarCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> Hogar:
    hogar = hogar_de_usuario(db, current.id)
    if hogar is None:
        hogar = Hogar(usuario_id=current.id, **data.model_dump())
        db.add(hogar)
    else:
        hogar.tamano = data.tamano
        hogar.presupuesto_semanal = data.presupuesto_semanal
        hogar.restricciones = data.restricciones
        hogar.equipo = data.equipo
    db.commit()
    db.refresh(hogar)
    return hogar

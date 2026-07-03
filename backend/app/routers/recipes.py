"""Endpoints de recetas (§6 + Fase 6 caso Walmart).

- POST /recipes/generate — motor LLM + caché (Fases 1-5, lo usa el rescate).
- GET  /recipes/{id} — detalle enriquecido (imagen, rating, comercio).
- POST /recipes — subir receta de comunidad (queda pendiente de moderación §9).
- GET/POST /recipes/{id}/reviews — reseñas tipo Google/Uber (1-5 ⭐).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.comercio import Comercio
from app.models.receta import EstadoAprobacion, Receta
from app.models.resena import ResenaReceta
from app.models.usuario import RolUsuario, Usuario
from app.schemas.recipes import GenerateRequest, GenerateResponse, RecetaOut
from app.schemas.social import RecetaUpload, ResenaCreate, ResenaOut
from app.services import recipe_engine

router = APIRouter(
    tags=["recipes"],
    dependencies=[Depends(require_rol(RolUsuario.cliente, RolUsuario.admin))],
)


def _rating(db: Session, receta_id: int) -> tuple[float | None, int]:
    avg, count = db.execute(
        select(func.avg(ResenaReceta.estrellas), func.count(ResenaReceta.id)).where(
            ResenaReceta.receta_id == receta_id
        )
    ).one()
    return (round(float(avg), 1) if avg is not None else None), int(count or 0)


def _es_comunidad(receta: Receta) -> bool:
    """Regla única (igual que el feed): sin comercio y con tag 'comunidad'."""
    return receta.comercio_id is None and "comunidad" in (receta.tags or [])


def _visible_para(receta: Receta | None, current: Usuario) -> Receta:
    """Moderación en lectura: lo no aprobado solo lo ve su autor o el admin."""
    if receta is None or (
        receta.estado_aprobacion != EstadoAprobacion.aprobada
        and current.rol != RolUsuario.admin
        and receta.autor_id != current.id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Receta no encontrada")
    return receta


@router.post(
    "/recipes/generate",
    response_model=GenerateResponse,
    summary="Genera recetas desde ingredientes (LLM + caché)",
)
def generar(
    data: GenerateRequest,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> GenerateResponse:
    return recipe_engine.generar_recetas(db, data, current)


@router.post(
    "/recipes",
    response_model=RecetaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Subir receta de comunidad (pasa a moderación)",
)
def subir_receta(
    data: RecetaUpload,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> RecetaOut:
    receta = Receta(
        titulo=data.titulo.strip(),
        pasos=data.pasos,
        ingredientes=data.ingredientes,
        porciones=data.porciones,
        imagen_url=data.imagen_url,
        estado_aprobacion=EstadoAprobacion.pendiente,  # la aprueba el admin (§9)
        autor_id=current.id,
        tags=["comunidad"],
    )
    db.add(receta)
    db.commit()
    db.refresh(receta)
    out = RecetaOut.model_validate(receta)
    out.comunidad = True
    return out


@router.get(
    "/recipes/{receta_id}",
    response_model=RecetaOut,
    summary="Detalle de receta (imagen, precio, rating, comercio)",
)
def detalle(
    receta_id: int,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> RecetaOut:
    receta = _visible_para(db.get(Receta, receta_id), current)
    out = RecetaOut.model_validate(receta)
    out.rating_avg, out.rating_count = _rating(db, receta.id)
    if receta.comercio_id is not None:
        comercio = db.get(Comercio, receta.comercio_id)
        out.comercio_nombre = comercio.nombre if comercio else None
    out.comunidad = _es_comunidad(receta)
    return out


@router.get(
    "/recipes/{receta_id}/reviews",
    response_model=list[ResenaOut],
    summary="Reseñas de la receta (recientes primero)",
)
def listar_resenas(
    receta_id: int,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> list[ResenaOut]:
    _visible_para(db.get(Receta, receta_id), current)
    filas = db.execute(
        select(ResenaReceta, Usuario)
        .join(Usuario, Usuario.id == ResenaReceta.usuario_id)
        .where(ResenaReceta.receta_id == receta_id)
        .order_by(ResenaReceta.created_at.desc())
        .limit(50)
    ).all()
    return [
        ResenaOut(
            id=r.id,
            usuario_nombre=u.nombre,
            avatar=u.avatar,
            estrellas=r.estrellas,
            comentario=r.comentario,
            created_at=r.created_at,
        )
        for r, u in filas
    ]


@router.post(
    "/recipes/{receta_id}/reviews",
    response_model=ResenaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Publicar/actualizar mi reseña (1-5 estrellas)",
)
def publicar_resena(
    receta_id: int,
    data: ResenaCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> ResenaOut:
    receta = db.get(Receta, receta_id)
    if receta is None or receta.estado_aprobacion != EstadoAprobacion.aprobada:
        # Solo se opina sobre recetas publicadas (no borradores ni despublicadas).
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Receta no encontrada")
    # Upsert: una reseña por usuario por receta (como en Google/Uber).
    resena = db.scalar(
        select(ResenaReceta).where(
            ResenaReceta.receta_id == receta_id,
            ResenaReceta.usuario_id == current.id,
        )
    )
    if resena is None:
        resena = ResenaReceta(receta_id=receta_id, usuario_id=current.id)
        db.add(resena)
    resena.estrellas = data.estrellas
    resena.comentario = (data.comentario or "").strip() or None
    db.commit()
    db.refresh(resena)
    return ResenaOut(
        id=resena.id,
        usuario_nombre=current.nombre,
        avatar=current.avatar,
        estrellas=resena.estrellas,
        comentario=resena.comentario,
        created_at=resena.created_at,
    )

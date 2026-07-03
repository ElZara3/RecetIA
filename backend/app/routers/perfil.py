"""Perfil del usuario (Fase 6 — caso Walmart).

- PATCH /me — actualizar nombre y/o avatar (emoji).
- GET /me/stats — estadísticas personales para la pantalla de perfil.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import UsuarioOut
from app.core.db import get_db
from app.models.plan import EventoAhorro
from app.models.receta import EstadoAprobacion, Receta
from app.models.resena import ResenaReceta
from app.models.usuario import Usuario
from app.schemas.social import MeStats, PerfilPatch

router = APIRouter(tags=["perfil"])


@router.patch("/me", response_model=UsuarioOut, summary="Actualizar nombre/avatar")
def actualizar_perfil(
    data: PerfilPatch,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> Usuario:
    if data.nombre is not None:
        current.nombre = data.nombre.strip()
    if data.avatar is not None:
        current.avatar = data.avatar.strip()
    db.commit()
    db.refresh(current)
    return current


@router.get("/me/stats", response_model=MeStats, summary="Mis estadísticas")
def mis_stats(
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> MeStats:
    monto, kg, eventos = db.execute(
        select(
            func.coalesce(func.sum(EventoAhorro.monto_ahorrado), 0.0),
            func.coalesce(func.sum(EventoAhorro.kg_rescatados), 0.0),
            func.count(EventoAhorro.id),
        ).where(EventoAhorro.usuario_id == current.id)
    ).one()
    resenas = db.scalar(
        select(func.count(ResenaReceta.id)).where(
            ResenaReceta.usuario_id == current.id
        )
    )
    # Solo cuentan las recetas de comunidad (subidas desde la app), no las
    # generadas por IA. El tag vive en JSON → se filtra en Python (SQLite-safe).
    mias = db.execute(
        select(Receta.tags, Receta.estado_aprobacion).where(
            Receta.autor_id == current.id
        )
    ).all()
    comunidad = [
        (tags, estado) for tags, estado in mias if "comunidad" in (tags or [])
    ]
    aprobadas = sum(
        1 for _, estado in comunidad if estado == EstadoAprobacion.aprobada
    )
    return MeStats(
        ahorro_total_mxn=round(float(monto), 2),
        kg_rescatados=round(float(kg), 2),
        veces_cocinadas=int(eventos),
        resenas_publicadas=int(resenas or 0),
        recetas_subidas=len(comunidad),
        recetas_aprobadas=aprobadas,
    )

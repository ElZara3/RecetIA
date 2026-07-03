"""Reporte de ahorro (§6 /savings + Fase 6). Rol cliente/admin.

Fase 6 (caso Walmart): el ahorro es del USUARIO (ya no requiere hogar).
Si el usuario tiene hogar (flujo legado de despensa), también se estampa.
"""

from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.plan import EventoAhorro
from app.models.receta import Receta
from app.models.usuario import RolUsuario, Usuario
from app.routers.hogar import hogar_de_usuario
from app.schemas.plan import AhorroCreate, AhorroReporte, EventoAhorroOut

router = APIRouter(
    tags=["savings"],
    dependencies=[Depends(require_rol(RolUsuario.cliente, RolUsuario.admin))],
)


def _filtro_mios(db: Session, current: Usuario):
    """Eventos del usuario: por usuario_id (Fase 6) o por su hogar (legado)."""
    hogar = hogar_de_usuario(db, current.id)
    if hogar is not None:
        return or_(
            EventoAhorro.usuario_id == current.id, EventoAhorro.hogar_id == hogar.id
        )
    return EventoAhorro.usuario_id == current.id


@router.post(
    "/savings",
    response_model=EventoAhorroOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un ahorro (p.ej. al cocinar una receta)",
)
def registrar_ahorro(
    data: AhorroCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> EventoAhorro:
    hogar = hogar_de_usuario(db, current.id)
    descripcion = data.descripcion
    receta_id = None
    if data.receta_id is not None:
        receta = db.get(Receta, data.receta_id)
        if receta is not None:
            receta_id = receta.id
            if not descripcion:
                descripcion = f"Cociné: {receta.titulo}"[:200]
    evento = EventoAhorro(
        usuario_id=current.id,
        hogar_id=hogar.id if hogar else None,
        receta_id=receta_id,
        fecha=data.fecha or date.today(),
        monto_ahorrado=data.monto_ahorrado,
        kg_rescatados=data.kg_rescatados,
        descripcion=descripcion,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


@router.get("/savings", response_model=AhorroReporte, summary="Mi reporte de ahorro")
def reporte_ahorro(
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> AhorroReporte:
    filtro = _filtro_mios(db, current)
    total_monto, total_kg, n = db.execute(
        select(
            func.coalesce(func.sum(EventoAhorro.monto_ahorrado), 0.0),
            func.coalesce(func.sum(EventoAhorro.kg_rescatados), 0.0),
            func.count(EventoAhorro.id),
        ).where(filtro)
    ).one()
    recientes = db.scalars(
        select(EventoAhorro)
        .where(filtro)
        .order_by(EventoAhorro.fecha.desc(), EventoAhorro.id.desc())
        .limit(10)
    ).all()
    return AhorroReporte(
        total_ahorrado_mxn=round(float(total_monto), 2),
        total_kg_rescatados=round(float(total_kg), 2),
        eventos=int(n),
        recientes=[EventoAhorroOut.model_validate(e) for e in recientes],
    )

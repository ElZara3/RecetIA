"""Reporte de ahorro (§6 /savings). Rol cliente/admin."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.hogar import Hogar
from app.models.plan import EventoAhorro
from app.models.usuario import RolUsuario, Usuario
from app.routers.hogar import hogar_de_usuario
from app.schemas.plan import AhorroCreate, AhorroReporte, EventoAhorroOut

router = APIRouter(
    tags=["savings"],
    dependencies=[Depends(require_rol(RolUsuario.cliente, RolUsuario.admin))],
)


def _hogar(db: Session, current: Usuario) -> Hogar:
    hogar = hogar_de_usuario(db, current.id)
    if hogar is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Crea tu hogar (onboarding) primero.")
    return hogar


@router.post("/savings", response_model=EventoAhorroOut, status_code=status.HTTP_201_CREATED,
             summary="Registrar un evento de ahorro (p.ej. al cocinar una receta)")
def registrar_ahorro(
    data: AhorroCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> EventoAhorro:
    hogar = _hogar(db, current)
    evento = EventoAhorro(
        hogar_id=hogar.id,
        fecha=data.fecha or date.today(),
        monto_ahorrado=data.monto_ahorrado,
        kg_rescatados=data.kg_rescatados,
        descripcion=data.descripcion,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


@router.get("/savings", response_model=AhorroReporte, summary="Reporte de ahorro del hogar")
def reporte_ahorro(
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> AhorroReporte:
    hogar = _hogar(db, current)
    total_monto = db.scalar(
        select(func.coalesce(func.sum(EventoAhorro.monto_ahorrado), 0.0)).where(
            EventoAhorro.hogar_id == hogar.id
        )
    ) or 0.0
    total_kg = db.scalar(
        select(func.coalesce(func.sum(EventoAhorro.kg_rescatados), 0.0)).where(
            EventoAhorro.hogar_id == hogar.id
        )
    ) or 0.0
    n = db.scalar(
        select(func.count()).select_from(EventoAhorro).where(EventoAhorro.hogar_id == hogar.id)
    ) or 0
    recientes = db.scalars(
        select(EventoAhorro)
        .where(EventoAhorro.hogar_id == hogar.id)
        .order_by(EventoAhorro.fecha.desc(), EventoAhorro.id.desc())
        .limit(10)
    ).all()
    return AhorroReporte(
        total_ahorrado_mxn=round(float(total_monto), 2),
        total_kg_rescatados=round(float(total_kg), 2),
        eventos=int(n),
        recientes=[EventoAhorroOut.model_validate(e) for e in recientes],
    )

"""Suscripción / paywall Plus (§8.6). Rol cliente/admin.

MVP: el upgrade es un stub (sin cobro real; §14 deja el carrito/pagos fuera).
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.plan import PlanSuscripcion, Suscripcion
from app.models.usuario import RolUsuario, Usuario
from app.schemas.plan import SuscripcionOut, SuscripcionUpgrade

router = APIRouter(
    prefix="/subscription",
    tags=["subscription"],
    dependencies=[Depends(require_rol(RolUsuario.cliente, RolUsuario.admin))],
)


def _get_or_create(db: Session, usuario_id: int) -> Suscripcion:
    sus = db.scalar(select(Suscripcion).where(Suscripcion.usuario_id == usuario_id))
    if sus is None:
        sus = Suscripcion(usuario_id=usuario_id, plan=PlanSuscripcion.gratis)
        db.add(sus)
        db.commit()
        db.refresh(sus)
    return sus


@router.get("", response_model=SuscripcionOut, summary="Mi suscripción")
def mi_suscripcion(
    db: Session = Depends(get_db), current: Usuario = Depends(get_current_user)
) -> Suscripcion:
    return _get_or_create(db, current.id)


@router.post("/upgrade", response_model=SuscripcionOut, summary="Cambiar a Plus (stub de pago)")
def upgrade(
    data: SuscripcionUpgrade,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> Suscripcion:
    sus = _get_or_create(db, current.id)
    sus.plan = data.plan
    sus.periodo = data.periodo
    sus.estado = "activa"
    db.commit()
    db.refresh(sus)
    return sus

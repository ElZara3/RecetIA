"""Notificaciones "úsalo primero" (§2 FCM). Rol cliente/admin."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.hogar import Hogar
from app.models.plan import DispositivoToken
from app.models.usuario import RolUsuario, Usuario
from app.routers.hogar import hogar_de_usuario
from app.schemas.plan import Notificacion, TokenRegister
from app.services import notifications

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    dependencies=[Depends(require_rol(RolUsuario.cliente, RolUsuario.admin))],
)


def _hogar(db: Session, current: Usuario) -> Hogar:
    hogar = hogar_de_usuario(db, current.id)
    if hogar is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Crea tu hogar (onboarding) primero.")
    return hogar


@router.get("", response_model=list[Notificacion], summary="Avisos 'úsalo primero'")
def listar(
    db: Session = Depends(get_db), current: Usuario = Depends(get_current_user)
) -> list[dict]:
    hogar = _hogar(db, current)
    return notifications.alertas_usalo_primero(db, hogar.id)


@router.post("/register-token", status_code=status.HTTP_204_NO_CONTENT,
             summary="Registrar token de dispositivo (FCM)")
def registrar_token(
    data: TokenRegister,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> None:
    existente = db.scalar(select(DispositivoToken).where(DispositivoToken.token == data.token))
    if existente is None:
        db.add(
            DispositivoToken(
                usuario_id=current.id, token=data.token, plataforma=data.plataforma
            )
        )
    else:
        existente.usuario_id = current.id
        existente.plataforma = data.plataforma
    db.commit()


@router.post("/test", summary="Enviar un push de prueba (stub si no hay FCM_SERVER_KEY)")
def test_push(
    db: Session = Depends(get_db), current: Usuario = Depends(get_current_user)
) -> dict:
    hogar = _hogar(db, current)
    avisos = notifications.alertas_usalo_primero(db, hogar.id)
    if avisos:
        a = avisos[0]
        titulo, mensaje = a["titulo"], a["mensaje"]
    else:
        titulo, mensaje = "RecetIA", "No tienes items por caducar. ¡Buen trabajo!"
    return notifications.enviar_push(db, current.id, titulo, mensaje)

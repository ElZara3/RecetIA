"""Notificaciones "úsalo primero" (Fase 5, §2 FCM).

- `alertas_usalo_primero`: calcula avisos de items por caducar (tono positivo).
- `enviar_push`: envía vía FCM si hay `FCM_SERVER_KEY`; si no, queda en stub (log).
"""

import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.item_despensa import ItemDespensa
from app.models.plan import DispositivoToken

logger = logging.getLogger("recetia.notifications")

DIAS_POR_CADUCAR = 4


def alertas_usalo_primero(db: Session, hogar_id: int) -> list[dict]:
    """Avisos para los items de la despensa próximos a caducar (§8 'úsalo primero')."""
    limite = date.today() + timedelta(days=DIAS_POR_CADUCAR)
    items = db.scalars(
        select(ItemDespensa)
        .where(
            ItemDespensa.hogar_id == hogar_id,
            ItemDespensa.fecha_caducidad.is_not(None),
            ItemDespensa.fecha_caducidad <= limite,
        )
        .order_by(ItemDespensa.fecha_caducidad.asc())
    ).all()

    avisos = []
    for it in items:
        dias = (it.fecha_caducidad - date.today()).days
        cuando = "hoy" if dias <= 0 else ("mañana" if dias == 1 else f"en {dias} días")
        avisos.append(
            {
                "tipo": "usalo_primero",
                "titulo": f"Aprovecha tu {it.nombre} 🌿",
                "mensaje": f"Tu {it.nombre} se usa mejor {cuando}. ¡Pídenos una receta para aprovecharlo!",
                "producto": it.nombre,
                "fecha_caducidad": it.fecha_caducidad,
            }
        )
    return avisos


def enviar_push(db: Session, usuario_id: int, titulo: str, mensaje: str) -> dict:
    """Envía un push a los dispositivos del usuario. Stub si no hay FCM_SERVER_KEY."""
    tokens = list(
        db.scalars(
            select(DispositivoToken.token).where(DispositivoToken.usuario_id == usuario_id)
        ).all()
    )
    if not tokens:
        return {"enviadas": 0, "fuente": "sin-dispositivos"}

    if not settings.fcm_server_key:
        logger.info("[FCM stub] %s -> %s | %s", tokens, titulo, mensaje)
        return {"enviadas": 0, "fuente": "stub", "tokens": len(tokens)}

    # Envío real vía FCM. NOTA: el endpoint legacy (fcm/send con "key=") está
    # deprecado por Google; al activar el envío real, migrar a HTTP v1
    # (/v1/projects/{id}/messages:send con OAuth2 de cuenta de servicio).
    import httpx

    enviadas = 0
    headers = {
        "Authorization": f"key={settings.fcm_server_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=10) as client:
        for tok in tokens:
            payload = {"to": tok, "notification": {"title": titulo, "body": mensaje}}
            try:
                r = client.post("https://fcm.googleapis.com/fcm/send", json=payload, headers=headers)
                if r.is_success:
                    enviadas += 1
            except Exception:  # pragma: no cover — no romper por un token
                logger.warning("FCM falló para un token", exc_info=True)
    return {"enviadas": enviadas, "fuente": "fcm", "tokens": len(tokens)}

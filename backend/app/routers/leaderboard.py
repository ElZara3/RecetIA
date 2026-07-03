"""Leaderboard / podio (Fase 6 — caso Walmart).

GET /leaderboard?tipo=ahorro|eco — top de usuarios por MXN ahorrados o por
kg de comida rescatada. Si el usuario actual no está en el top, se incluye
aparte (campo `yo`) para que la app siempre muestre su posición.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.db import get_db
from app.models.plan import EventoAhorro
from app.models.usuario import Usuario
from app.schemas.social import LeaderboardEntry, LeaderboardOut

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard", response_model=LeaderboardOut, summary="Podio de usuarios")
def leaderboard(
    tipo: str = Query(default="ahorro"),
    limit: int = Query(default=10, ge=3, le=50),
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> LeaderboardOut:
    tipo = tipo if tipo in ("ahorro", "eco") else "ahorro"
    columna = (
        EventoAhorro.monto_ahorrado if tipo == "ahorro" else EventoAhorro.kg_rescatados
    )

    filas = db.execute(
        select(
            Usuario.id,
            Usuario.nombre,
            Usuario.avatar,
            func.sum(columna).label("valor"),
        )
        .join(Usuario, Usuario.id == EventoAhorro.usuario_id)
        .where(EventoAhorro.usuario_id.is_not(None))
        .group_by(Usuario.id, Usuario.nombre, Usuario.avatar)
        # Sin filas en cero (p.ej. tipo=eco cuando solo registró dinero).
        .having(func.sum(columna) > 0)
        .order_by(func.sum(columna).desc())
        .limit(limit)
    ).all()

    top: list[LeaderboardEntry] = []
    yo: LeaderboardEntry | None = None
    for pos, (uid, nombre, avatar, valor) in enumerate(filas, start=1):
        entry = LeaderboardEntry(
            posicion=pos,
            nombre=nombre,
            avatar=avatar,
            valor=round(float(valor or 0), 2),
            es_usuario=(uid == current.id),
        )
        top.append(entry)
        if entry.es_usuario:
            yo = entry

    if yo is None:
        # El usuario no está en el top: calcula su total y posición real.
        total = db.scalar(
            select(func.coalesce(func.sum(columna), 0.0)).where(
                EventoAhorro.usuario_id == current.id
            )
        )
        total = float(total or 0)
        if total > 0:
            mejores = db.scalar(
                select(func.count())
                .select_from(
                    select(EventoAhorro.usuario_id)
                    .where(EventoAhorro.usuario_id.is_not(None))
                    .group_by(EventoAhorro.usuario_id)
                    .having(func.sum(columna) > total)
                    .subquery()
                )
            )
            yo = LeaderboardEntry(
                posicion=int(mejores or 0) + 1,
                nombre=current.nombre,
                avatar=current.avatar,
                valor=round(total, 2),
                es_usuario=True,
            )

    return LeaderboardOut(tipo=tipo, top=top, yo=yo)

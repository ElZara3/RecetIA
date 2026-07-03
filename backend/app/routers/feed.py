"""Feed del consumidor (Fase 6 — caso Walmart).

GET /feed — recetas publicadas (de la tienda y de la comunidad) con imagen,
precio por porción, rating, badges de rescate 🌿 y la oferta ligada si existe.
Es la portada de la app móvil.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.comercio import Comercio, Oferta
from app.models.receta import EstadoAprobacion, Receta
from app.models.resena import ResenaReceta
from app.models.usuario import RolUsuario
from app.schemas.social import FeedItem, OfertaFeed

router = APIRouter(
    tags=["feed"],
    dependencies=[
        Depends(require_rol(RolUsuario.cliente, RolUsuario.admin)),
        Depends(get_current_user),
    ],
)

_FILTROS = {"todas", "ofertas", "comunidad", "top", "nuevas"}


@router.get("/feed", response_model=list[FeedItem], summary="Feed de recetas de la app")
def feed(
    filtro: str = Query(default="todas"),
    limit: int = Query(default=30, ge=1, le=60),
    db: Session = Depends(get_db),
) -> list[FeedItem]:
    filtro = filtro if filtro in _FILTROS else "todas"

    # Recetas aprobadas + rating agregado + nombre del comercio (una sola pasada).
    rating_sq = (
        select(
            ResenaReceta.receta_id.label("rid"),
            func.avg(ResenaReceta.estrellas).label("avg"),
            func.count(ResenaReceta.id).label("cnt"),
        )
        .group_by(ResenaReceta.receta_id)
        .subquery()
    )
    # Cap consciente para el MVP: se trabaja sobre las 200 aprobadas más
    # recientes; con catálogo grande los filtros deben empujarse al SQL.
    filas = db.execute(
        select(Receta, Comercio.nombre, rating_sq.c.avg, rating_sq.c.cnt)
        .outerjoin(Comercio, Comercio.id == Receta.comercio_id)
        .outerjoin(rating_sq, rating_sq.c.rid == Receta.id)
        .where(Receta.estado_aprobacion == EstadoAprobacion.aprobada)
        .order_by(Receta.created_at.desc())
        .limit(200)
    ).all()

    # Ofertas vigentes ligadas a esas recetas (la mejor por receta = mayor descuento).
    ids = [r.id for r, *_ in filas]
    ofertas: dict[int, Oferta] = {}
    if ids:
        for o in db.scalars(
            select(Oferta).where(
                Oferta.receta_id.in_(ids),
                (Oferta.vence.is_(None)) | (Oferta.vence >= date.today()),
            )
        ).all():
            actual = ofertas.get(o.receta_id)
            if actual is None or o.precio_oferta < actual.precio_oferta:
                ofertas[o.receta_id] = o

    items: list[FeedItem] = []
    for receta, comercio_nombre, avg, cnt in filas:
        tags = receta.tags or []
        oferta = ofertas.get(receta.id)
        # Defensa multi-tenant: la oferta solo se muestra si es DEL comercio
        # de la receta (una oferta ajena no debe colgarse de otra tienda).
        if oferta is not None and oferta.comercio_id != receta.comercio_id:
            oferta = None
        oferta_out = None
        if oferta is not None:
            descuento = None
            if oferta.precio_normal and oferta.precio_normal > 0:
                descuento = round(
                    (1 - oferta.precio_oferta / oferta.precio_normal) * 100
                )
            oferta_out = OfertaFeed(
                producto=oferta.producto,
                precio_oferta=oferta.precio_oferta,
                precio_normal=oferta.precio_normal,
                descuento_pct=descuento,
                vence=oferta.vence,
            )
        items.append(
            FeedItem(
                id=receta.id,
                titulo=receta.titulo,
                imagen_url=receta.imagen_url,
                costo_porcion=receta.costo_porcion,
                porciones=receta.porciones,
                ahorro_estimado_mxn=receta.ahorro_estimado_mxn,
                rating_avg=round(float(avg), 1) if avg is not None else None,
                rating_count=int(cnt or 0),
                comercio_nombre=comercio_nombre,
                comunidad=receta.comercio_id is None and "comunidad" in tags,
                rescate="rescate" in tags,
                tags=tags,
                oferta=oferta_out,
            )
        )

    # Filtros + orden de la portada.
    if filtro == "ofertas":
        items = [i for i in items if i.oferta is not None]
    elif filtro == "comunidad":
        items = [i for i in items if i.comunidad]
    elif filtro == "top":
        items.sort(key=lambda i: (-(i.rating_avg or 0), -i.rating_count))
    if filtro in ("todas", "ofertas"):
        # Rescate primero (es la misión del producto), luego mejor calificadas.
        items.sort(key=lambda i: (not i.rescate, -(i.rating_avg or 0)))
    return items[:limit]

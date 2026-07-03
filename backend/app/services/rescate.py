"""Rescate de inventario (Fase 6 — caso Walmart).

Flujo: el comercio detecta productos por caducar → el LLM genera recetas que los
aprovechan → las recetas se publican (aprobadas, ligadas al comercio) → se crean
ofertas con descuento sobre esos productos, enlazadas a las recetas.

La app del consumidor muestra todo esto en el feed: receta + precio + oferta.
"""

from datetime import date, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.comercio import Comercio, Oferta, ProductoInventario
from app.models.receta import EstadoAprobacion, Receta
from app.models.usuario import Usuario
from app.schemas.recipes import GenerateRequest, ItemDespensaInput
from app.services.recipe_engine import generar_recetas

# Ventana de riesgo: productos que caducan en <= N días.
DIAS_RIESGO = 5
# Descuento aplicado al crear la oferta de rescate (25%).
FACTOR_OFERTA = 0.75


def productos_en_riesgo(
    db: Session, comercio_id: int, dias: int = DIAS_RIESGO
) -> list[ProductoInventario]:
    """Productos con existencias que caducan dentro de la ventana de riesgo."""
    limite = date.today() + timedelta(days=dias)
    return list(
        db.scalars(
            select(ProductoInventario)
            .where(
                ProductoInventario.comercio_id == comercio_id,
                ProductoInventario.existencias > 0,
                ProductoInventario.fecha_caducidad.is_not(None),
                # Riesgo accionable: caduca pronto pero AÚN NO ha caducado
                # (lo vencido es merma, no receta — seguridad alimentaria).
                ProductoInventario.fecha_caducidad >= date.today(),
                ProductoInventario.fecha_caducidad <= limite,
            )
            .order_by(ProductoInventario.fecha_caducidad)
        ).all()
    )


def generar_rescate(
    db: Session,
    current: Usuario,
    comercio: Comercio,
    n_recetas: int = 3,
    dias: int = DIAS_RIESGO,
) -> dict:
    """Genera recetas de rescate + ofertas desde los productos en riesgo."""
    riesgo = productos_en_riesgo(db, comercio.id, dias)
    if not riesgo:
        return {
            "productos_en_riesgo": [],
            "recetas": [],
            "ofertas_creadas": 0,
            "fuente": "sin-riesgo",
        }

    # 1. Generar recetas con el motor existente (LLM o stub), usando los
    #    productos en riesgo como "despensa" con sus caducidades reales.
    despensa = [
        ItemDespensaInput(
            nombre=p.nombre,
            cantidad=p.existencias,
            unidad="pza",
            fecha_caducidad=p.fecha_caducidad,
        )
        for p in riesgo
    ]
    resp = generar_recetas(
        db, GenerateRequest(despensa=despensa, n_recetas=n_recetas), current
    )

    # 2. Publicar: recetas de la tienda salen aprobadas y ligadas al comercio.
    recetas_db: list[Receta] = []
    for g in resp.recetas:
        receta = db.get(Receta, g.id)
        if receta is None:  # pragma: no cover — el engine las acaba de persistir
            continue
        # Multi-tenant seguro: la caché del motor puede devolver filas de OTRO
        # dueño (otro comercio con los mismos productos, o el borrador de un
        # cliente). En ese caso se CLONA una fila nueva en vez de apropiarse:
        # el dashboard/reseñas del dueño original quedan intactos.
        es_propia = receta.comercio_id == comercio.id or (
            receta.comercio_id is None and receta.autor_id == current.id
        )
        if not es_propia:
            receta = Receta(
                titulo=receta.titulo,
                pasos=list(receta.pasos or []),
                ingredientes=list(receta.ingredientes or []),
                costo_porcion=receta.costo_porcion,
                porciones=receta.porciones,
                ahorro_estimado_mxn=receta.ahorro_estimado_mxn,
                imagen_url=receta.imagen_url,
                autor_id=current.id,
                tags=list(receta.tags or []),
            )
            db.add(receta)
            db.flush()
        receta.estado_aprobacion = EstadoAprobacion.aprobada
        receta.comercio_id = comercio.id
        if "rescate" not in (receta.tags or []):
            receta.tags = [*(receta.tags or []), "rescate"]
        recetas_db.append(receta)

    # 3. Ofertas: un descuento por producto en riesgo, enlazado a la receta
    #    que lo aprovecha (o a la primera de rescate como fallback).
    ofertas_creadas = 0
    for p in riesgo:
        if p.precio is None or p.precio <= 0:
            continue  # sin precio no hay oferta que publicar
        # Evitar duplicar la oferta vigente del mismo producto (vigente =
        # sin vencimiento o venciendo hoy o después, igual que el feed).
        existente = db.scalar(
            select(Oferta).where(
                Oferta.comercio_id == comercio.id,
                Oferta.producto == p.nombre,
                or_(Oferta.vence.is_(None), Oferta.vence >= date.today()),
            )
        )
        if existente is not None:
            continue
        receta_link = _receta_que_usa(recetas_db, p.nombre)
        db.add(
            Oferta(
                comercio_id=comercio.id,
                producto=p.nombre,
                precio_oferta=round(p.precio * FACTOR_OFERTA, 2),
                precio_normal=p.precio,
                vence=p.fecha_caducidad,
                receta_id=receta_link.id if receta_link else None,
            )
        )
        ofertas_creadas += 1

    db.commit()
    return {
        "productos_en_riesgo": [p.nombre for p in riesgo],
        "recetas": [{"id": r.id, "titulo": r.titulo} for r in recetas_db],
        "ofertas_creadas": ofertas_creadas,
        "fuente": resp.fuente,
    }


def _receta_que_usa(recetas: list[Receta], producto: str) -> Receta | None:
    """Primera receta cuyos ingredientes mencionan el producto (por tokens)."""
    tokens = {t for t in producto.lower().split() if len(t) >= 3}
    for r in recetas:
        for ing in r.ingredientes or []:
            if tokens & {t for t in ing.lower().split() if len(t) >= 3}:
                return r
    return recetas[0] if recetas else None

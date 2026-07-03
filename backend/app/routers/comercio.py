"""Endpoints del lado comercio (§6/§10 + Fase 6 caso Walmart). Rol comercio (o admin)."""

import random
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.comercio import (
    Comercio,
    Oferta,
    ProductoInventario,
    VentaRegistro,
)
from app.models.plan import EventoAhorro
from app.models.receta import Receta
from app.models.resena import ResenaReceta
from app.models.usuario import RolUsuario, Usuario
from app.schemas.comercio import (
    ComercioCreate,
    ComercioOut,
    ForecastResponse,
    OfertaCreate,
    OfertaOut,
    ProductoCreate,
    ProductoOut,
    VentaCreate,
    VentaOut,
)
from app.schemas.social import (
    DashboardComercio,
    ProductoRiesgo,
    RecetaComercioOut,
    RescateRequest,
    RescateResumen,
)
from app.services import forecasting, rescate

router = APIRouter(
    prefix="/comercio",
    tags=["comercio"],
    dependencies=[Depends(require_rol(RolUsuario.comercio, RolUsuario.admin))],
)

# Productos de muestra para el seed del demo.
_PRODUCTOS_DEMO = {
    "jitomate": 40, "cebolla": 30, "huevo": 60, "tortilla": 90, "leche": 50,
    "frijol": 25, "arroz": 28, "pollo": 35, "aguacate": 22, "chile": 18,
}


def _mi_comercio(db: Session, current: Usuario) -> Comercio | None:
    return db.scalar(select(Comercio).where(Comercio.usuario_id == current.id))


def _comercio_obligatorio(db: Session, current: Usuario) -> Comercio:
    comercio = _mi_comercio(db, current)
    if comercio is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Crea tu comercio (POST /comercio) antes de continuar.",
        )
    return comercio


# --------------------------- Perfil del comercio --------------------------- #


@router.get("", response_model=ComercioOut, summary="Mi comercio")
def mi_comercio(
    db: Session = Depends(get_db), current: Usuario = Depends(get_current_user)
) -> Comercio:
    comercio = _mi_comercio(db, current)
    if comercio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aún no has creado tu comercio")
    return comercio


@router.post("", response_model=ComercioOut, summary="Crear/actualizar mi comercio")
def crear_o_actualizar(
    data: ComercioCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> Comercio:
    comercio = _mi_comercio(db, current)
    if comercio is None:
        comercio = Comercio(usuario_id=current.id, **data.model_dump())
        db.add(comercio)
    else:
        comercio.nombre = data.nombre
        comercio.tipo = data.tipo
        comercio.ubicacion = data.ubicacion
    db.commit()
    db.refresh(comercio)
    return comercio


# --------------------------- Inventario --------------------------- #


@router.get("/inventory", response_model=list[ProductoOut], summary="Inventario")
def listar_inventario(
    db: Session = Depends(get_db), current: Usuario = Depends(get_current_user)
) -> list[ProductoInventario]:
    comercio = _comercio_obligatorio(db, current)
    return list(
        db.scalars(
            select(ProductoInventario)
            .where(ProductoInventario.comercio_id == comercio.id)
            .order_by(ProductoInventario.nombre)
        ).all()
    )


@router.post(
    "/inventory",
    response_model=ProductoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar producto al inventario",
)
def agregar_producto(
    data: ProductoCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> ProductoInventario:
    comercio = _comercio_obligatorio(db, current)
    # Upsert por (comercio, nombre): si ya existe, actualiza en vez de duplicar.
    prod = db.scalar(
        select(ProductoInventario).where(
            ProductoInventario.comercio_id == comercio.id,
            ProductoInventario.nombre == data.nombre,
        )
    )
    if prod is None:
        prod = ProductoInventario(comercio_id=comercio.id, **data.model_dump())
        db.add(prod)
    else:
        prod.existencias = data.existencias
        prod.fecha_caducidad = data.fecha_caducidad
        prod.precio = data.precio
    db.commit()
    db.refresh(prod)
    return prod


# --------------------------- Ventas --------------------------- #


@router.post(
    "/sales",
    response_model=VentaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar venta (alimenta el forecasting)",
)
def registrar_venta(
    data: VentaCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> VentaRegistro:
    comercio = _comercio_obligatorio(db, current)
    venta = VentaRegistro(
        comercio_id=comercio.id,
        producto=data.producto,
        cantidad=data.cantidad,
        fecha=data.fecha or date.today(),
    )
    db.add(venta)
    db.commit()
    db.refresh(venta)
    return venta


# --------------------------- Forecast --------------------------- #


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="Predicción de demanda + recomendación de reabasto",
)
def forecast(
    db: Session = Depends(get_db), current: Usuario = Depends(get_current_user)
) -> ForecastResponse:
    comercio = _comercio_obligatorio(db, current)
    return ForecastResponse(**forecasting.generar_forecast(db, comercio.id))


# --------------------------- Ofertas --------------------------- #


@router.get("/offers", response_model=list[OfertaOut], summary="Listar ofertas")
def listar_ofertas(
    db: Session = Depends(get_db), current: Usuario = Depends(get_current_user)
) -> list[Oferta]:
    comercio = _comercio_obligatorio(db, current)
    return list(
        db.scalars(
            select(Oferta).where(Oferta.comercio_id == comercio.id).order_by(Oferta.id.desc())
        ).all()
    )


@router.post(
    "/offers",
    response_model=OfertaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Publicar oferta de producto por vencer",
)
def publicar_oferta(
    data: OfertaCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> Oferta:
    comercio = _comercio_obligatorio(db, current)
    oferta = Oferta(comercio_id=comercio.id, **data.model_dump())
    db.add(oferta)
    db.commit()
    db.refresh(oferta)
    return oferta


# --------------------------- Seed demo --------------------------- #


@router.post("/seed-demo", summary="Poblar inventario + ventas de muestra (demo)")
def seed_demo(
    db: Session = Depends(get_db), current: Usuario = Depends(get_current_user)
) -> dict:
    comercio = _comercio_obligatorio(db, current)
    rng = random.Random(42)

    # Limpia datos previos del comercio (idempotente).
    db.execute(delete(ProductoInventario).where(ProductoInventario.comercio_id == comercio.id))
    db.execute(delete(VentaRegistro).where(VentaRegistro.comercio_id == comercio.id))

    hoy = date.today()
    quincena = (14, 15, 16, 29, 30, 31, 1)
    mes_factor = {
        1: 0.95, 2: 0.92, 3: 0.98, 4: 1.0, 5: 1.05, 6: 1.0,
        7: 1.02, 8: 1.0, 9: 1.03, 10: 1.05, 11: 1.1, 12: 1.25,
    }

    ventas_n = 0
    for i, (prod, nivel) in enumerate(_PRODUCTOS_DEMO.items()):
        # Inventario: algo de stock; los 2 primeros caducan pronto (demo de merma).
        existencias = float(nivel * rng.uniform(2, 4))
        caduca = hoy + timedelta(days=(3 if i < 2 else rng.randint(10, 40)))
        db.add(
            ProductoInventario(
                comercio_id=comercio.id,
                nombre=prod,
                existencias=round(existencias),
                fecha_caducidad=caduca,
                precio=round(rng.uniform(8, 60), 2),
            )
        )
        # Ventas de los últimos 120 días con el patrón estacional.
        for k in range(120, 0, -1):
            d = hoy - timedelta(days=k)
            factor = mes_factor[d.month]
            if d.weekday() >= 5:
                factor *= 1.3
            if d.day in quincena:
                factor *= 1.25
            cantidad = max(0, round(nivel * factor * rng.gauss(1.0, 0.15)))
            if cantidad > 0:
                db.add(
                    VentaRegistro(
                        comercio_id=comercio.id, producto=prod, fecha=d, cantidad=cantidad
                    )
                )
                ventas_n += 1

    db.commit()
    return {
        "comercio_id": comercio.id,
        "productos": len(_PRODUCTOS_DEMO),
        "ventas_creadas": ventas_n,
    }


# ----------------- Fase 6 — caso Walmart: dashboard + rescate ----------------- #


@router.get(
    "/recipes",
    response_model=list[RecetaComercioOut],
    summary="Recetas publicadas por mi comercio (con rating y desempeño)",
)
def mis_recetas(
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> list[RecetaComercioOut]:
    comercio = _comercio_obligatorio(db, current)
    recetas = db.scalars(
        select(Receta)
        .where(Receta.comercio_id == comercio.id)
        .order_by(Receta.created_at.desc())
        .limit(100)
    ).all()
    salida: list[RecetaComercioOut] = []
    for r in recetas:
        avg, cnt = db.execute(
            select(func.avg(ResenaReceta.estrellas), func.count(ResenaReceta.id)).where(
                ResenaReceta.receta_id == r.id
            )
        ).one()
        cocinadas = db.scalar(
            select(func.count(EventoAhorro.id)).where(EventoAhorro.receta_id == r.id)
        )
        salida.append(
            RecetaComercioOut(
                id=r.id,
                titulo=r.titulo,
                rating_avg=round(float(avg), 1) if avg is not None else None,
                rating_count=int(cnt or 0),
                veces_cocinadas=int(cocinadas or 0),
                rescate="rescate" in (r.tags or []),
                created_at=r.created_at,
            )
        )
    return salida


@router.post(
    "/rescate",
    response_model=RescateResumen,
    summary="Generar recetas + ofertas desde productos por caducar",
)
def generar_rescate(
    data: RescateRequest | None = None,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> RescateResumen:
    comercio = _comercio_obligatorio(db, current)
    params = data or RescateRequest()
    resumen = rescate.generar_rescate(
        db, current, comercio, n_recetas=params.n_recetas, dias=params.dias
    )
    return RescateResumen(**resumen)


@router.get(
    "/dashboard",
    response_model=DashboardComercio,
    summary="KPIs del comercio (inventario, riesgo, recetas, impacto)",
)
def dashboard(
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> DashboardComercio:
    comercio = _comercio_obligatorio(db, current)
    hoy = date.today()

    productos_total = int(
        db.scalar(
            select(func.count(ProductoInventario.id)).where(
                ProductoInventario.comercio_id == comercio.id
            )
        )
        or 0
    )
    riesgo = rescate.productos_en_riesgo(db, comercio.id)
    ofertas_activas = int(
        db.scalar(
            select(func.count(Oferta.id)).where(
                Oferta.comercio_id == comercio.id,
                (Oferta.vence.is_(None)) | (Oferta.vence >= hoy),
            )
        )
        or 0
    )
    recetas_ids = list(
        db.scalars(select(Receta.id).where(Receta.comercio_id == comercio.id)).all()
    )
    recetas_publicadas = len(recetas_ids)

    rating_promedio: float | None = None
    resenas_total = 0
    veces_cocinadas = 0
    ahorro_clientes = 0.0
    kg_rescatados = 0.0
    if recetas_ids:
        avg, cnt = db.execute(
            select(func.avg(ResenaReceta.estrellas), func.count(ResenaReceta.id)).where(
                ResenaReceta.receta_id.in_(recetas_ids)
            )
        ).one()
        rating_promedio = round(float(avg), 1) if avg is not None else None
        resenas_total = int(cnt or 0)
        monto, kg, n = db.execute(
            select(
                func.coalesce(func.sum(EventoAhorro.monto_ahorrado), 0.0),
                func.coalesce(func.sum(EventoAhorro.kg_rescatados), 0.0),
                func.count(EventoAhorro.id),
            ).where(EventoAhorro.receta_id.in_(recetas_ids))
        ).one()
        ahorro_clientes = round(float(monto), 2)
        kg_rescatados = round(float(kg), 2)
        veces_cocinadas = int(n)

    return DashboardComercio(
        productos_total=productos_total,
        en_riesgo_total=len(riesgo),
        en_riesgo=[
            ProductoRiesgo(
                nombre=p.nombre,
                existencias=p.existencias,
                fecha_caducidad=p.fecha_caducidad,
                dias_restantes=(
                    (p.fecha_caducidad - hoy).days if p.fecha_caducidad else None
                ),
                precio=p.precio,
            )
            for p in riesgo[:10]
        ],
        ofertas_activas=ofertas_activas,
        recetas_publicadas=recetas_publicadas,
        rating_promedio=rating_promedio,
        resenas_total=resenas_total,
        veces_cocinadas=veces_cocinadas,
        ahorro_clientes_mxn=ahorro_clientes,
        kg_rescatados=kg_rescatados,
    )

"""Plan semanal + lista de compras (§6 /plan, §8.5). Rol cliente/admin."""

import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.hogar import Hogar
from app.models.item_despensa import ItemDespensa
from app.models.plan import PlanSemanal
from app.models.receta import Receta
from app.models.usuario import RolUsuario, Usuario
from app.routers.hogar import hogar_de_usuario
from app.schemas.plan import ListaCompras, PlanCreate, PlanOut, RecetaEnPlan

router = APIRouter(
    tags=["plan"],
    dependencies=[Depends(require_rol(RolUsuario.cliente, RolUsuario.admin))],
)


def _hogar(db: Session, current: Usuario) -> Hogar:
    hogar = hogar_de_usuario(db, current.id)
    if hogar is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Crea tu hogar (onboarding) primero.")
    return hogar


def _semana_actual() -> str:
    iso = date.today().isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _tokens(texto: str) -> set[str]:
    """Palabras de >=3 letras (evita falsos positivos por subcadena como 'sal' en 'ensalada')."""
    return set(re.findall(r"[a-záéíóúñ]{3,}", texto.lower()))


# Categorías simples para agrupar la lista de compras (§8.5 "agrupado").
_CATEGORIAS = {
    "Lácteos y huevo": ["leche", "queso", "yogur", "crema", "mantequilla", "huevo"],
    "Carnes y pescado": ["pollo", "res", "cerdo", "pescado", "carne", "jamón", "atún"],
    "Frutas y verduras": [
        "jitomate", "tomate", "cebolla", "aguacate", "chile", "lechuga", "manzana",
        "plátano", "papa", "zanahoria", "limón", "nopal", "calabaza", "espinaca", "ajo",
    ],
    "Abarrotes": ["arroz", "frijol", "aceite", "sal", "azúcar", "pasta", "harina", "tortilla", "pan", "pimienta"],
}


def _categoria(ingrediente: str) -> str:
    low = ingrediente.lower()
    for cat, palabras in _CATEGORIAS.items():
        if any(p in low for p in palabras):
            return cat
    return "Otros"


def _plan_a_out(db: Session, plan: PlanSemanal) -> PlanOut:
    recetas = (
        db.scalars(select(Receta).where(Receta.id.in_(plan.recetas))).all()
        if plan.recetas
        else []
    )
    # Conserva el orden del plan.
    por_id = {r.id: r for r in recetas}
    ordenadas = [por_id[i] for i in plan.recetas if i in por_id]
    return PlanOut(
        id=plan.id,
        hogar_id=plan.hogar_id,
        semana=plan.semana,
        recetas=[RecetaEnPlan.model_validate(r) for r in ordenadas],
    )


@router.post("/plan", response_model=PlanOut, summary="Crear/actualizar el plan semanal")
def crear_plan(
    data: PlanCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> PlanOut:
    hogar = _hogar(db, current)
    semana = data.semana or _semana_actual()

    # Valida que las recetas existan.
    existentes = set(
        db.scalars(select(Receta.id).where(Receta.id.in_(data.recetas))).all()
    )
    faltan = [r for r in data.recetas if r not in existentes]
    if faltan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Recetas inexistentes: {faltan}")

    plan = db.scalar(
        select(PlanSemanal).where(
            PlanSemanal.hogar_id == hogar.id, PlanSemanal.semana == semana
        )
    )
    if plan is None:
        plan = PlanSemanal(hogar_id=hogar.id, semana=semana, recetas=data.recetas)
        db.add(plan)
    else:
        plan.recetas = data.recetas
    db.commit()
    db.refresh(plan)
    return _plan_a_out(db, plan)


@router.get("/plan", response_model=PlanOut, summary="Plan semanal (semana actual o ?semana=)")
def obtener_plan(
    semana: str | None = None,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> PlanOut:
    hogar = _hogar(db, current)
    objetivo = semana or _semana_actual()
    plan = db.scalar(
        select(PlanSemanal).where(
            PlanSemanal.hogar_id == hogar.id, PlanSemanal.semana == objetivo
        )
    )
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay plan para esa semana")
    return _plan_a_out(db, plan)


@router.get(
    "/plan/shopping-list",
    response_model=ListaCompras,
    summary="Lista de compras: solo lo que falta del plan",
)
def lista_compras(
    semana: str | None = None,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> ListaCompras:
    hogar = _hogar(db, current)
    objetivo = semana or _semana_actual()
    plan = db.scalar(
        select(PlanSemanal).where(
            PlanSemanal.hogar_id == hogar.id, PlanSemanal.semana == objetivo
        )
    )
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay plan para esa semana")

    recetas = (
        db.scalars(select(Receta).where(Receta.id.in_(plan.recetas))).all()
        if plan.recetas
        else []
    )
    # Ingredientes necesarios (dedup, conservando el texto original).
    necesarios: dict[str, str] = {}
    for r in recetas:
        for ing in r.ingredientes:
            clave = ing.strip().lower()
            if clave:
                necesarios.setdefault(clave, ing.strip())

    # Tokens (palabras completas) de los nombres de la despensa.
    despensa_tokens: set[str] = set()
    for i in db.scalars(
        select(ItemDespensa).where(ItemDespensa.hogar_id == hogar.id)
    ).all():
        despensa_tokens |= _tokens(i.nombre)

    def en_despensa(ing_low: str) -> bool:
        return bool(_tokens(ing_low) & despensa_tokens)

    faltan = sorted(orig for low, orig in necesarios.items() if not en_despensa(low))
    ya_tienes = sorted(orig for low, orig in necesarios.items() if en_despensa(low))

    # Agrupado por categoría (§8.5).
    por_categoria: dict[str, list[str]] = {}
    for ing in faltan:
        por_categoria.setdefault(_categoria(ing), []).append(ing)

    return ListaCompras(
        semana=objetivo, faltan=faltan, ya_tienes=ya_tienes, por_categoria=por_categoria
    )

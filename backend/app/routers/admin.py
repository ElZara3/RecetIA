"""Endpoints del panel admin (§6/§9). Todo el router exige rol admin (RBAC)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.hogar import Hogar
from app.models.item_despensa import ItemDespensa
from app.models.plan import EventoAhorro, PlanSuscripcion, Suscripcion
from app.models.receta import EstadoAprobacion, Receta
from app.models.receta_cache import RecetaCache
from app.models.usuario import RolUsuario, Usuario
from app.schemas.admin import (
    MetricsOut,
    RecetaAdminOut,
    RecetaPatch,
    UsuarioAdminOut,
    UsuarioPatch,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_rol(RolUsuario.admin))],
)


# --------------------------- Usuarios --------------------------- #


@router.get("/users", response_model=list[UsuarioAdminOut], summary="Listar usuarios")
def listar_usuarios(db: Session = Depends(get_db)) -> list[Usuario]:
    return list(db.scalars(select(Usuario).order_by(Usuario.id)).all())


@router.patch(
    "/users/{user_id}",
    response_model=UsuarioAdminOut,
    summary="Cambiar rol / suspender usuario",
)
def patch_usuario(
    user_id: int,
    data: UsuarioPatch,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> Usuario:
    user = db.get(Usuario, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")

    # Roles asignables en el MVP (editor está diseñado pero deshabilitado, §4/§14).
    if data.rol is not None and data.rol not in {
        RolUsuario.cliente,
        RolUsuario.comercio,
        RolUsuario.admin,
    }:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Rol no asignable en el MVP (usa cliente, comercio o admin).",
        )

    # Evita que un admin se bloquee a sí mismo (perder acceso al panel).
    if user.id == current.id:
        if data.activo is False:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes suspenderte a ti mismo.")
        if data.rol is not None and data.rol != RolUsuario.admin:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes quitarte tu propio rol de admin.")

    if data.rol is not None:
        user.rol = data.rol
    if data.activo is not None:
        user.activo = data.activo
    db.commit()
    db.refresh(user)
    return user


# --------------------------- Recetas (moderación) --------------------------- #


@router.get("/recipes", response_model=list[RecetaAdminOut], summary="Listar recetas (moderación)")
def listar_recetas(
    estado: EstadoAprobacion | None = None,
    db: Session = Depends(get_db),
) -> list[Receta]:
    query = select(Receta).order_by(Receta.id.desc())
    if estado is not None:
        query = query.where(Receta.estado_aprobacion == estado)
    return list(db.scalars(query).all())


@router.patch(
    "/recipes/{receta_id}",
    response_model=RecetaAdminOut,
    summary="Moderar receta (aprobar / despublicar)",
)
def moderar_receta(
    receta_id: int,
    data: RecetaPatch,
    db: Session = Depends(get_db),
) -> Receta:
    receta = db.get(Receta, receta_id)
    if receta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Receta no encontrada")
    receta.estado_aprobacion = data.estado_aprobacion
    db.commit()
    db.refresh(receta)
    return receta


# --------------------------- Métricas --------------------------- #


@router.get("/metrics", response_model=MetricsOut, summary="Métricas del panel")
def metrics(db: Session = Depends(get_db)) -> MetricsOut:
    def count(modelo) -> int:
        return db.scalar(select(func.count()).select_from(modelo)) or 0

    por_rol = {
        rol.value: c
        for rol, c in db.execute(
            select(Usuario.rol, func.count()).group_by(Usuario.rol)
        ).all()
    }
    por_estado = {
        estado.value: c
        for estado, c in db.execute(
            select(Receta.estado_aprobacion, func.count()).group_by(Receta.estado_aprobacion)
        ).all()
    }

    generaciones_unicas = count(RecetaCache)
    reusos = db.scalar(select(func.coalesce(func.sum(RecetaCache.hits), 0))) or 0
    kg = db.scalar(select(func.coalesce(func.sum(EventoAhorro.kg_rescatados), 0.0))) or 0.0
    ahorro = db.scalar(select(func.coalesce(func.sum(EventoAhorro.monto_ahorrado), 0.0))) or 0.0
    plus = db.scalar(
        select(func.count())
        .select_from(Suscripcion)
        .where(Suscripcion.plan == PlanSuscripcion.plus)
    ) or 0

    # Nota: MAU y "recetas top" (§6) se difieren (requieren tracking de sesiones /
    # uso por receta, aún no construidos). El resto sale de datos reales.
    return MetricsOut(
        usuarios_total=count(Usuario),
        usuarios_por_rol=por_rol,
        hogares_total=count(Hogar),
        items_despensa_total=count(ItemDespensa),
        recetas_total=count(Receta),
        recetas_por_estado=por_estado,
        generaciones_unicas=generaciones_unicas,
        recetas_servidas=generaciones_unicas + int(reusos),
        kg_rescatados=round(float(kg), 2),
        ahorro_total_mxn=round(float(ahorro), 2),
        suscripciones_plus=int(plus),
    )

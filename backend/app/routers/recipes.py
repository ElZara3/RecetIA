"""Endpoints de recetas (§6): POST /recipes/generate, GET /recipes/{id}."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_rol
from app.core.db import get_db
from app.models.receta import Receta
from app.models.usuario import RolUsuario, Usuario
from app.schemas.recipes import GenerateRequest, GenerateResponse, RecetaOut
from app.services import recipe_engine

router = APIRouter(
    tags=["recipes"],
    dependencies=[Depends(require_rol(RolUsuario.cliente, RolUsuario.admin))],
)


@router.post(
    "/recipes/generate",
    response_model=GenerateResponse,
    summary="Genera recetas desde la despensa (LLM + caché)",
)
def generar(
    data: GenerateRequest,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> GenerateResponse:
    return recipe_engine.generar_recetas(db, data, current)


@router.get(
    "/recipes/{receta_id}",
    response_model=RecetaOut,
    summary="Detalle de receta",
)
def detalle(
    receta_id: int,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
) -> Receta:
    receta = db.get(Receta, receta_id)
    if receta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Receta no encontrada")
    return receta

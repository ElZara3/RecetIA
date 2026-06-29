"""Esquemas del panel admin (§9)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator

from app.models.receta import EstadoAprobacion
from app.models.usuario import RolUsuario


class UsuarioAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nombre: str
    rol: RolUsuario
    activo: bool
    created_at: datetime


class UsuarioPatch(BaseModel):
    """Cambiar rol y/o suspender (al menos uno)."""

    rol: RolUsuario | None = None
    activo: bool | None = None

    @model_validator(mode="after")
    def _al_menos_uno(self) -> "UsuarioPatch":
        if self.rol is None and self.activo is None:
            raise ValueError("Envía 'rol' y/o 'activo'.")
        return self


class RecetaAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    estado_aprobacion: EstadoAprobacion
    autor_id: int | None
    tags: list[str]
    created_at: datetime


class RecetaPatch(BaseModel):
    estado_aprobacion: EstadoAprobacion


class MetricsOut(BaseModel):
    usuarios_total: int
    usuarios_por_rol: dict[str, int]
    hogares_total: int
    items_despensa_total: int
    recetas_total: int
    recetas_por_estado: dict[str, int]
    generaciones_unicas: int  # combinaciones distintas generadas (entradas de caché)
    recetas_servidas: int  # generaciones + reúsos de caché
    kg_rescatados: float  # suma de EventoAhorro (Fase 5)
    ahorro_total_mxn: float  # suma de EventoAhorro (Fase 5)
    suscripciones_plus: int  # conversión a Plus (Fase 5)

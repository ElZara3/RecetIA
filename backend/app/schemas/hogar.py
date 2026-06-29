"""Esquemas del Hogar (§5) — usados por el onboarding (§8)."""

from pydantic import BaseModel, ConfigDict, Field


class HogarCreate(BaseModel):
    tamano: int = Field(default=1, ge=1, le=20)
    presupuesto_semanal: float | None = Field(default=None, ge=0)
    restricciones: list[str] = Field(default_factory=list)
    equipo: list[str] = Field(default_factory=list)


class HogarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    tamano: int
    presupuesto_semanal: float | None
    restricciones: list[str]
    equipo: list[str]

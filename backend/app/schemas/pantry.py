"""Esquemas de la despensa (§5/§6) — pantalla "Mi despensa" (§8)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemDespensaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    cantidad: float | None = Field(default=None, ge=0)
    unidad: str | None = Field(default=None, max_length=40)
    fecha_caducidad: date | None = None


class ItemDespensaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hogar_id: int
    nombre: str
    cantidad: float | None
    unidad: str | None
    fecha_caducidad: date | None
    created_at: datetime

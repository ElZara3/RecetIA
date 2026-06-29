"""Esquemas del lado comercio (§5/§6/§10)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Comercio (perfil) ---
class ComercioCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=160)
    tipo: str | None = Field(default=None, max_length=80)
    ubicacion: str | None = Field(default=None, max_length=200)


class ComercioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    nombre: str
    tipo: str | None
    ubicacion: str | None


# --- Inventario ---
class ProductoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    existencias: float = Field(default=0, ge=0)
    fecha_caducidad: date | None = None
    precio: float | None = Field(default=None, ge=0)


class ProductoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    comercio_id: int
    nombre: str
    existencias: float
    fecha_caducidad: date | None
    precio: float | None


# --- Ventas ---
class VentaCreate(BaseModel):
    producto: str = Field(min_length=1, max_length=120)
    cantidad: float = Field(gt=0)
    fecha: date | None = None  # default: hoy


class VentaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    comercio_id: int
    producto: str
    fecha: date
    cantidad: float


# --- Ofertas ---
class OfertaCreate(BaseModel):
    producto: str = Field(min_length=1, max_length=120)
    precio_oferta: float = Field(gt=0)
    vence: date | None = None


class OfertaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    comercio_id: int
    producto: str
    precio_oferta: float
    vence: date | None


# --- Forecast ---
class ForecastDia(BaseModel):
    fecha: str
    demanda: float


class ForecastProducto(BaseModel):
    producto: str
    nivel_base: float
    demanda_estimada: float
    existencias: float
    recomendacion_reabasto: str
    riesgo_merma: bool
    motivo_merma: str | None = None


class ForecastResponse(BaseModel):
    comercio_id: int
    periodo: str
    fuente: str
    serie_diaria: list[ForecastDia]
    productos: list[ForecastProducto]

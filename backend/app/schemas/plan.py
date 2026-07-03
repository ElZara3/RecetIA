"""Esquemas de Fase 5: plan semanal + lista de compras, ahorro, notificaciones,
suscripción, OCR de ticket."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.plan import PlanSuscripcion


# --- Plan semanal (§8.5) ---
class PlanCreate(BaseModel):
    recetas: list[int] = Field(min_length=1)
    semana: str | None = None  # ISO "AAAA-Www"; por defecto la semana actual


class RecetaEnPlan(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    costo_porcion: float | None
    porciones: int | None


class PlanOut(BaseModel):
    id: int
    hogar_id: int
    semana: str
    recetas: list[RecetaEnPlan]


class ListaCompras(BaseModel):
    semana: str
    # Solo lo que falta: ingredientes de las recetas del plan que NO están en la despensa.
    faltan: list[str]
    ya_tienes: list[str]
    # Lo que falta, agrupado por categoría (§8.5).
    por_categoria: dict[str, list[str]] = {}


# --- Ahorro (§6 /savings) ---
class AhorroCreate(BaseModel):
    # Topes por evento: el ahorro es autorreportado y alimenta el podio (anti-trampa).
    monto_ahorrado: float = Field(ge=0, le=2000)
    kg_rescatados: float = Field(default=0, ge=0, le=50)
    descripcion: str | None = Field(default=None, max_length=200)
    fecha: date | None = None
    # Fase 6: receta que se cocinó ("cociné esto") — habilita KPIs por comercio.
    receta_id: int | None = None


class EventoAhorroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: date
    monto_ahorrado: float
    kg_rescatados: float
    descripcion: str | None


class AhorroReporte(BaseModel):
    total_ahorrado_mxn: float
    total_kg_rescatados: float
    eventos: int
    recientes: list[EventoAhorroOut]


# --- Notificaciones (§2 FCM "úsalo primero") ---
class TokenRegister(BaseModel):
    token: str = Field(min_length=1, max_length=255)
    plataforma: str = Field(default="android", max_length=20)


class Notificacion(BaseModel):
    tipo: str  # "usalo_primero"
    titulo: str
    mensaje: str
    producto: str | None = None
    fecha_caducidad: date | None = None


# --- Suscripción (§8.6 paywall Plus) ---
class SuscripcionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan: PlanSuscripcion
    estado: str
    periodo: str | None


class SuscripcionUpgrade(BaseModel):
    plan: PlanSuscripcion = PlanSuscripcion.plus
    periodo: str | None = "mensual"


# --- OCR scan-ticket (§6, fase 2) ---
class ScanResultado(BaseModel):
    items: list[str]  # nombres detectados / agregados a la despensa
    agregados: int
    texto_ocr: str | None = None

"""Esquemas del motor de recetas (§7)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.receta import EstadoAprobacion


class ItemDespensaInput(BaseModel):
    """Item de despensa enviado en línea (sin necesidad de persistir todavía)."""

    nombre: str = Field(min_length=1, max_length=120)
    cantidad: float | None = None
    unidad: str | None = Field(default=None, max_length=40)
    fecha_caducidad: date | None = None


class GenerateRequest(BaseModel):
    """Entrada de POST /recipes/generate.

    Acepta la despensa en línea (`despensa`) y/o un `hogar_id` para cargarla de la BD.
    """

    hogar_id: int | None = None
    despensa: list[ItemDespensaInput] = Field(default_factory=list)
    restricciones: list[str] = Field(default_factory=list)
    presupuesto_semanal: float | None = None
    n_recetas: int = Field(default=3, ge=1, le=5)

    @field_validator("restricciones")
    @classmethod
    def _cap_restricciones(cls, v: list[str]) -> list[str]:
        # Defensa en profundidad ante inyección de prompt vía texto libre.
        return [r[:80] for r in v[:20]]


class RecetaLLM(BaseModel):
    """Esquema estricto que pedimos al LLM (JSON de la §7)."""

    titulo: str
    ingredientes_usados: list[str]
    ingredientes_faltantes: list[str]
    pasos: list[str]
    porciones: int
    costo_porcion_mxn: float
    ahorro_estimado_mxn: float
    usa_por_caducar: list[str]


class RecetasLLM(BaseModel):
    """Contenedor: el LLM devuelve {"recetas": [...]}"""

    recetas: list[RecetaLLM]


class RecetaGenerada(RecetaLLM):
    """Receta de la respuesta, con el id de la Receta persistida."""

    id: int | None = None


class GenerateResponse(BaseModel):
    recetas: list[RecetaGenerada]
    cache_hit: bool = False
    fuente: str  # "llm:<modelo>" o "stub"


class RecetaOut(BaseModel):
    """Detalle de receta persistida (forma del modelo §5).

    Las recetas generadas por IA son genéricas y compartibles (la caché las reúsa
    entre usuarios), por eso GET /recipes/{id} es legible por cualquier autenticado.
    No exponemos `autor_id` para no filtrar de qué usuario provino. La moderación y
    el control por rol llegan en Fase 3.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    pasos: list[str]
    ingredientes: list[str]
    costo_porcion: float | None
    porciones: int | None
    estado_aprobacion: EstadoAprobacion
    tags: list[str]
    created_at: datetime

"""Esquemas de la Fase 6 — caso Walmart.

Feed del consumidor, reseñas (tipo Google/Uber), recetas de comunidad,
perfil con avatar, estadísticas, leaderboard y dashboard del comercio.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


# --------------------------------------------------------------------------- #
# Reseñas
# --------------------------------------------------------------------------- #


class ResenaCreate(BaseModel):
    estrellas: int = Field(ge=1, le=5)
    comentario: str | None = Field(default=None, max_length=400)


class ResenaOut(BaseModel):
    id: int
    usuario_nombre: str
    avatar: str
    estrellas: int
    comentario: str | None
    created_at: datetime


# --------------------------------------------------------------------------- #
# Feed del consumidor
# --------------------------------------------------------------------------- #


class OfertaFeed(BaseModel):
    producto: str
    precio_oferta: float
    precio_normal: float | None = None
    descuento_pct: int | None = None  # calculado si hay precio_normal
    vence: date | None = None


class FeedItem(BaseModel):
    id: int
    titulo: str
    imagen_url: str | None = None
    costo_porcion: float | None = None
    porciones: int | None = None
    ahorro_estimado_mxn: float | None = None
    rating_avg: float | None = None
    rating_count: int = 0
    comercio_nombre: str | None = None  # null => receta de la comunidad
    comunidad: bool = False
    rescate: bool = False  # usa productos por caducar ("rescátalo" 🌿)
    tags: list[str] = []
    oferta: OfertaFeed | None = None


# --------------------------------------------------------------------------- #
# Recetas de comunidad (subidas por usuarios)
# --------------------------------------------------------------------------- #


class RecetaUpload(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    ingredientes: list[str] = Field(min_length=1, max_length=30)
    pasos: list[str] = Field(min_length=1, max_length=20)
    porciones: int | None = Field(default=None, ge=1, le=20)
    imagen_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _limpiar(self) -> "RecetaUpload":
        self.titulo = self.titulo.strip()
        if len(self.titulo) < 3:
            raise ValueError("El título necesita al menos 3 caracteres.")
        self.ingredientes = [i.strip()[:120] for i in self.ingredientes if i.strip()]
        self.pasos = [p.strip()[:400] for p in self.pasos if p.strip()]
        if not self.ingredientes or not self.pasos:
            raise ValueError("La receta necesita al menos un ingrediente y un paso.")
        return self


# --------------------------------------------------------------------------- #
# Perfil + estadísticas del usuario
# --------------------------------------------------------------------------- #


class PerfilPatch(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    avatar: str | None = Field(default=None, min_length=1, max_length=16)

    @model_validator(mode="after")
    def _al_menos_uno(self) -> "PerfilPatch":
        # Strip ANTES de validar: "  " no debe convertirse en nombre/avatar vacío.
        if self.nombre is not None:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                raise ValueError("El nombre no puede quedar vacío.")
        if self.avatar is not None:
            self.avatar = self.avatar.strip()
            if not self.avatar:
                raise ValueError("El avatar no puede quedar vacío.")
        if self.nombre is None and self.avatar is None:
            raise ValueError("Envía al menos un campo a actualizar.")
        return self


class MeStats(BaseModel):
    ahorro_total_mxn: float
    kg_rescatados: float
    veces_cocinadas: int
    resenas_publicadas: int
    recetas_subidas: int
    recetas_aprobadas: int


# --------------------------------------------------------------------------- #
# Leaderboard (podio)
# --------------------------------------------------------------------------- #


class LeaderboardEntry(BaseModel):
    posicion: int
    nombre: str
    avatar: str
    valor: float  # MXN ahorrados (tipo=ahorro) o kg rescatados (tipo=eco)
    es_usuario: bool = False  # resalta al usuario actual en la app


class LeaderboardOut(BaseModel):
    tipo: str  # "ahorro" | "eco"
    top: list[LeaderboardEntry]
    yo: LeaderboardEntry | None = None  # posición del usuario si no está en el top


# --------------------------------------------------------------------------- #
# Comercio: dashboard + rescate
# --------------------------------------------------------------------------- #


class ProductoRiesgo(BaseModel):
    nombre: str
    existencias: float
    fecha_caducidad: date | None
    dias_restantes: int | None
    precio: float | None


class DashboardComercio(BaseModel):
    productos_total: int
    en_riesgo_total: int
    en_riesgo: list[ProductoRiesgo]
    ofertas_activas: int
    recetas_publicadas: int
    rating_promedio: float | None
    resenas_total: int
    veces_cocinadas: int  # "cociné esto" sobre recetas del comercio
    ahorro_clientes_mxn: float
    kg_rescatados: float


class RescateRequest(BaseModel):
    n_recetas: int = Field(default=3, ge=1, le=5)
    dias: int = Field(default=5, ge=1, le=30)


class RecetaResumen(BaseModel):
    id: int
    titulo: str


class RescateResumen(BaseModel):
    productos_en_riesgo: list[str]
    recetas: list[RecetaResumen]
    ofertas_creadas: int
    fuente: str


class RecetaComercioOut(BaseModel):
    """Receta publicada por el comercio, con su desempeño (panel web)."""

    id: int
    titulo: str
    rating_avg: float | None
    rating_count: int
    veces_cocinadas: int
    rescate: bool
    created_at: datetime

"""Modelos ORM de RecetIA (§5 del SPEC).

Fase 0: Usuario, Hogar, ItemDespensa, Receta.
Importar este paquete registra todos los modelos en `Base.metadata`.
"""

from app.models.comercio import (
    Comercio,
    Oferta,
    Prediccion,
    ProductoInventario,
    VentaRegistro,
)
from app.models.hogar import Hogar
from app.models.item_despensa import ItemDespensa
from app.models.plan import (
    DispositivoToken,
    EventoAhorro,
    PlanSemanal,
    PlanSuscripcion,
    Suscripcion,
)
from app.models.receta import EstadoAprobacion, Receta
from app.models.receta_cache import RecetaCache
from app.models.resena import ResenaReceta
from app.models.usuario import RolUsuario, Usuario

__all__ = [
    "ResenaReceta",
    "Usuario",
    "RolUsuario",
    "Hogar",
    "ItemDespensa",
    "Receta",
    "EstadoAprobacion",
    "RecetaCache",
    "Comercio",
    "ProductoInventario",
    "VentaRegistro",
    "Prediccion",
    "Oferta",
    "PlanSemanal",
    "EventoAhorro",
    "Suscripcion",
    "PlanSuscripcion",
    "DispositivoToken",
]

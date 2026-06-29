"""Modelo Receta (§5).

Campos clave: id, titulo, pasos[], ingredientes[], costo_porcion, porciones,
estado_aprobacion, autor_id, tags[].
`autor_id` es opcional: las recetas generadas por el LLM (Fase 1) pueden no tener autor.
"""

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class EstadoAprobacion(str, enum.Enum):
    """Estado de moderación de la receta (§9 admin)."""

    borrador = "borrador"
    pendiente = "pendiente"
    aprobada = "aprobada"
    despublicada = "despublicada"


class Receta(Base):
    __tablename__ = "recetas"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    pasos: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    ingredientes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    costo_porcion: Mapped[float | None] = mapped_column(Float, nullable=True)
    porciones: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado_aprobacion: Mapped[EstadoAprobacion] = mapped_column(
        Enum(EstadoAprobacion, name="estado_aprobacion"),
        default=EstadoAprobacion.borrador,
        nullable=False,
    )
    autor_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    autor: Mapped["Usuario | None"] = relationship(back_populates="recetas")

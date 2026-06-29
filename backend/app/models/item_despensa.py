"""Modelo ItemDespensa (§5).

Campos clave: id, hogar_id, nombre, cantidad, unidad, fecha_caducidad, created_at.
La `fecha_caducidad` alimenta la priorización "úsalo primero" del motor de recetas (Fase 1).
"""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.hogar import Hogar


class ItemDespensa(Base):
    __tablename__ = "items_despensa"

    id: Mapped[int] = mapped_column(primary_key=True)
    hogar_id: Mapped[int] = mapped_column(
        ForeignKey("hogares.id", ondelete="CASCADE"), index=True, nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    cantidad: Mapped[float | None] = mapped_column(Float, nullable=True)
    unidad: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fecha_caducidad: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    hogar: Mapped["Hogar"] = relationship(back_populates="items_despensa")

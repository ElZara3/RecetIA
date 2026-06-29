"""Modelo Hogar (§5).

Campos clave: id, usuario_id, tamaño, presupuesto_semanal, restricciones[], equipo[].
Las listas se guardan como JSON (compatible con SQLite y PostgreSQL).
"""

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.item_despensa import ItemDespensa
    from app.models.usuario import Usuario


class Hogar(Base):
    __tablename__ = "hogares"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # `tamano` = tamaño del hogar (nº de personas). ASCII por portabilidad.
    tamano: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    presupuesto_semanal: Mapped[float | None] = mapped_column(Float, nullable=True)
    restricciones: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    equipo: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="hogares")
    items_despensa: Mapped[list["ItemDespensa"]] = relationship(
        back_populates="hogar", cascade="all, delete-orphan"
    )

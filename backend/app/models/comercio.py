"""Modelos del lado comercio (§5): Comercio, ProductoInventario, VentaRegistro,
Prediccion, Oferta.
"""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Comercio(Base):
    __tablename__ = "comercios"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    tipo: Mapped[str | None] = mapped_column(String(80), nullable=True)  # abarrotes, frutería…
    ubicacion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    usuario: Mapped["Usuario"] = relationship()
    inventario: Mapped[list["ProductoInventario"]] = relationship(
        back_populates="comercio", cascade="all, delete-orphan"
    )
    ventas: Mapped[list["VentaRegistro"]] = relationship(
        back_populates="comercio", cascade="all, delete-orphan"
    )


class ProductoInventario(Base):
    __tablename__ = "productos_inventario"
    # Un producto por nombre por comercio (evita filas duplicadas que el forecast
    # colapsaría, subestimando existencias).
    __table_args__ = (
        UniqueConstraint("comercio_id", "nombre", name="uq_producto_comercio_nombre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    comercio_id: Mapped[int] = mapped_column(
        ForeignKey("comercios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    existencias: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    fecha_caducidad: Mapped[date | None] = mapped_column(Date, nullable=True)
    precio: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    comercio: Mapped["Comercio"] = relationship(back_populates="inventario")


class VentaRegistro(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(primary_key=True)
    comercio_id: Mapped[int] = mapped_column(
        ForeignKey("comercios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    producto: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    fecha: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    cantidad: Mapped[float] = mapped_column(Float, nullable=False)

    comercio: Mapped["Comercio"] = relationship(back_populates="ventas")


class Prediccion(Base):
    __tablename__ = "predicciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    comercio_id: Mapped[int] = mapped_column(
        ForeignKey("comercios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    producto: Mapped[str] = mapped_column(String(120), nullable=False)
    periodo: Mapped[str] = mapped_column(String(40), nullable=False)  # p.ej. "próximos 7 días"
    demanda_estimada: Mapped[float] = mapped_column(Float, nullable=False)
    recomendacion_reabasto: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class Oferta(Base):
    __tablename__ = "ofertas"

    id: Mapped[int] = mapped_column(primary_key=True)
    comercio_id: Mapped[int] = mapped_column(
        ForeignKey("comercios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    producto: Mapped[str] = mapped_column(String(120), nullable=False)
    precio_oferta: Mapped[float] = mapped_column(Float, nullable=False)
    vence: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

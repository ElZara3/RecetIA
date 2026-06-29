"""Modelos de Fase 5 (§5): PlanSemanal, EventoAhorro, Suscripcion, DispositivoToken."""

import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PlanSemanal(Base):
    __tablename__ = "planes_semanales"
    # Un plan por hogar por semana.
    __table_args__ = (UniqueConstraint("hogar_id", "semana", name="uq_plan_hogar_semana"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    hogar_id: Mapped[int] = mapped_column(
        ForeignKey("hogares.id", ondelete="CASCADE"), index=True, nullable=False
    )
    semana: Mapped[str] = mapped_column(String(20), nullable=False)  # ISO, p.ej. "2026-W26"
    recetas: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)  # ids de Receta
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class EventoAhorro(Base):
    __tablename__ = "eventos_ahorro"

    id: Mapped[int] = mapped_column(primary_key=True)
    hogar_id: Mapped[int] = mapped_column(
        ForeignKey("hogares.id", ondelete="CASCADE"), index=True, nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    monto_ahorrado: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    kg_rescatados: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(200), nullable=True)


class PlanSuscripcion(str, enum.Enum):
    gratis = "gratis"
    plus = "plus"


class Suscripcion(Base):
    __tablename__ = "suscripciones"
    __table_args__ = (UniqueConstraint("usuario_id", name="uq_suscripcion_usuario"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    plan: Mapped[PlanSuscripcion] = mapped_column(
        Enum(PlanSuscripcion, name="plan_suscripcion"),
        default=PlanSuscripcion.gratis,
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(String(20), default="activa", nullable=False)
    periodo: Mapped[str | None] = mapped_column(String(20), nullable=True)  # p.ej. "mensual"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class DispositivoToken(Base):
    """Token de dispositivo para notificaciones push (FCM)."""

    __tablename__ = "dispositivos_token"
    __table_args__ = (UniqueConstraint("token", name="uq_dispositivo_token"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    plataforma: Mapped[str] = mapped_column(String(20), default="android", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

"""Modelo Usuario (§5).

Campos clave: id, email, password_hash, nombre, rol, created_at.
"""

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.hogar import Hogar
    from app.models.receta import Receta


class RolUsuario(str, enum.Enum):
    """Roles RBAC (§4). MVP: cliente, admin, comercio. editor → Fase 2."""

    cliente = "cliente"
    admin = "admin"
    comercio = "comercio"
    editor = "editor"  # Fase 2 — diseñado, deshabilitado


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(RolUsuario, name="rol_usuario"),
        default=RolUsuario.cliente,
        nullable=False,
    )
    # Suspender cuenta (admin). False => no puede iniciar sesión / usar la API.
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Caso Walmart (Fase 6): avatar del perfil (emoji elegido por el usuario).
    avatar: Mapped[str] = mapped_column(String(16), default="🧑‍🍳", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    hogares: Mapped[list["Hogar"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    recetas: Mapped[list["Receta"]] = relationship(back_populates="autor")

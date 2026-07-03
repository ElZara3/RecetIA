"""Modelo ResenaReceta (Fase 6 — caso Walmart).

Opiniones tipo Google/Uber sobre una receta: estrellas 1-5 + comentario corto.
Una reseña por usuario por receta (la segunda vez se actualiza, no se duplica).
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ResenaReceta(Base):
    __tablename__ = "resenas_receta"
    __table_args__ = (
        UniqueConstraint("receta_id", "usuario_id", name="uq_resena_receta_usuario"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    receta_id: Mapped[int] = mapped_column(
        ForeignKey("recetas.id", ondelete="CASCADE"), index=True, nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    estrellas: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..5
    comentario: Mapped[str | None] = mapped_column(String(400), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

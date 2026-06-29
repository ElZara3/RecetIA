"""Caché del motor de recetas (§7).

Clave = hash de (ingredientes + restricciones + n). Reusar combinaciones ya
generadas baja el costo de IA (objetivo ~$1/usuario/mes).
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RecetaCache(Base):
    __tablename__ = "recetas_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    # payload = GenerateResponse serializado (recetas con id + fuente)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    hits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

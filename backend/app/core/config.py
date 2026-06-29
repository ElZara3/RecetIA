"""Configuración de la app — lee variables de entorno / `.env` (§13 del SPEC).

Las llaves y secretos NUNCA se hardcodean: siempre vienen del entorno.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Secreto por defecto SOLO para desarrollo. En prod se exige sobrescribir JWT_SECRET
# (el validador de abajo falla al arrancar si se intenta usar este valor fuera de dev).
DEFAULT_DEV_JWT_SECRET = "dev-only-insecure-secret-change-me-in-production"


class Settings(BaseSettings):
    # App
    app_name: str = "RecetIA API"
    environment: str = "development"

    # Base de datos — dev: SQLite; prod: PostgreSQL (vía DATABASE_URL)
    database_url: str = "sqlite:///./recetia.db"

    # JWT / Auth
    jwt_secret: str = DEFAULT_DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 h

    # CORS — dominios permitidos (CORS_ORIGINS separado por comas). Dev: "*" (abierto).
    # NoDecode: evita que pydantic-settings intente json.loads de la variable de entorno.
    cors_origins: Annotated[list[str], NoDecode] = ["*"]

    # LLM (Fase 1) — clave del entorno, nunca hardcodeada. Si no hay clave, el
    # motor de recetas usa un stub determinista (fuente="stub") para dev/demo.
    llm_api_key: str | None = None
    llm_model: str = "claude-opus-4-8"

    # Fase 5 — OCR de ticket (Tesseract). Ruta opcional al binario tesseract.
    tesseract_cmd: str | None = None
    # Fase 5 — notificaciones push (FCM). Sin clave, el envío queda en stub/log.
    fcm_server_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, v: object) -> object:
        # CORS_ORIGINS="http://a.com, https://b.com" -> ["http://a.com", "https://b.com"]
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @model_validator(mode="after")
    def _enforce_prod_secret(self) -> "Settings":
        # En producción no se permite arrancar con el secreto de dev ni con uno débil.
        if self.environment != "development":
            if self.jwt_secret == DEFAULT_DEV_JWT_SECRET:
                raise ValueError(
                    "Define JWT_SECRET en el entorno: el secreto por defecto de dev "
                    "no se permite cuando ENVIRONMENT != 'development'."
                )
            if len(self.jwt_secret.encode("utf-8")) < 32:
                raise ValueError(
                    "JWT_SECRET debe tener al menos 32 bytes en producción (HS256)."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

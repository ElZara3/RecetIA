"""Esquemas Pydantic para autenticación (request/response)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.usuario import RolUsuario


def _normalize_email(v: object) -> object:
    """Email = identidad única → minúsculas + sin espacios (antes de validar formato)."""
    return v.strip().lower() if isinstance(v, str) else v


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(min_length=1, max_length=120)
    # §6: el registro "define rol". MVP: cliente | admin | comercio.
    # NOTA seguridad: permitir auto-registro como admin se debe restringir en Fase 3 (RBAC).
    rol: RolUsuario = RolUsuario.cliente

    _norm_email = field_validator("email", mode="before")(_normalize_email)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    _norm_email = field_validator("email", mode="before")(_normalize_email)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioOut(BaseModel):
    """Perfil público del usuario (sin password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nombre: str
    rol: RolUsuario
    created_at: datetime

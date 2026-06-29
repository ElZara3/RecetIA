"""Endpoints de autenticación (§6): /auth/register, /auth/login, /me."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import LoginRequest, RegisterRequest, Token, UsuarioOut
from app.core.db import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.usuario import Usuario

router = APIRouter(tags=["auth"])


@router.post(
    "/auth/register",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Alta de usuario (define rol)",
)
def register(data: RegisterRequest, db: Session = Depends(get_db)) -> Usuario:
    existing = db.scalar(select(Usuario).where(Usuario.email == data.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )
    user = Usuario(
        email=data.email,
        password_hash=hash_password(data.password),
        nombre=data.nombre,
        rol=data.rol,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=Token, summary="Login → devuelve JWT")
def login(data: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.scalar(select(Usuario).where(Usuario.email == data.email))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta suspendida.",
        )
    token = create_access_token(subject=str(user.id), extra={"rol": user.rol.value})
    return Token(access_token=token)


@router.get("/me", response_model=UsuarioOut, summary="Perfil + rol del usuario actual")
def me(current: Usuario = Depends(get_current_user)) -> Usuario:
    return current

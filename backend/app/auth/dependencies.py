"""Dependencias de autenticación de FastAPI.

`get_current_user` valida el JWT del header `Authorization: Bearer <token>` y
devuelve el Usuario. La validación de ROL por endpoint (RBAC) llega en la Fase 3.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.usuario import Usuario

bearer_scheme = HTTPBearer(auto_error=True)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudieron validar las credenciales",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    try:
        payload = decode_access_token(creds.credentials)
        sub = payload.get("sub")
        if sub is None:
            raise _credentials_exception
        user_id = int(sub)
    except (jwt.PyJWTError, ValueError, TypeError):
        raise _credentials_exception

    user = db.get(Usuario, user_id)
    if user is None:
        raise _credentials_exception
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta suspendida.",
        )
    return user

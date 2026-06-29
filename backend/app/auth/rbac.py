"""RBAC: dependencia de FastAPI que valida el rol por endpoint (§4).

Uso:
    router = APIRouter(dependencies=[Depends(require_rol(RolUsuario.admin))])
o por endpoint:
    def endpoint(current: Usuario = Depends(require_rol(RolUsuario.comercio, RolUsuario.admin))): ...
"""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.models.usuario import RolUsuario, Usuario


def require_rol(*roles: RolUsuario) -> Callable[..., Usuario]:
    """Crea una dependencia que exige que el usuario tenga uno de [roles]."""

    def dependency(current: Usuario = Depends(get_current_user)) -> Usuario:
        if current.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para esta acción.",
            )
        return current

    return dependency

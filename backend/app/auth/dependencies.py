"""
auth/dependencies.py — Dependencies de autenticação para injeção no FastAPI.

Uso nos routers:
    from app.auth.dependencies import get_current_user

    @router.get("/meu-endpoint")
    async def endpoint(user: UserInfo = Depends(get_current_user)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.schemas import UserInfo
from app.auth.service import obter_info_usuario

# Extrai o token do header "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserInfo:
    """
    Dependency que valida o JWT e retorna o usuário autenticado.

    Lança HTTP 401 se o token for inválido ou expirado.
    Deve ser usada em todos os endpoints protegidos.
    """
    token = credentials.credentials
    user = obter_info_usuario(token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

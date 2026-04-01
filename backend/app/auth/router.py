"""
auth/router.py — Endpoints de autenticação.

Rotas:
  POST /auth/login  — Autentica no AD e retorna JWT
  GET  /auth/me     — Retorna dados do usuário autenticado
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import LoginRequest, TokenResponse, UserInfo
from app.auth.service import autenticar_usuario, criar_token_acesso
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["Autenticação"])
settings = get_settings()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login via Active Directory",
    description=(
        "Autentica o usuário no servidor Active Directory configurado "
        "e retorna um token JWT para uso nas demais requisições."
    ),
)
async def login(body: LoginRequest) -> TokenResponse:
    """
    Realiza o login do usuário via Active Directory.

    - **username**: login de rede (sAMAccountName)
    - **password**: senha do domínio

    Retorna um Bearer token JWT com validade configurável.
    """
    resultado = autenticar_usuario(body.username, body.password)

    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou servidor AD inacessível.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = criar_token_acesso(
        username=body.username,
        nome=resultado["nome"],
        grupos=resultado["grupos"],
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get(
    "/me",
    response_model=UserInfo,
    summary="Dados do usuário autenticado",
    description="Retorna as informações do usuário extraídas do token JWT.",
)
async def me(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """Retorna nome, username e grupos do usuário autenticado."""
    return current_user

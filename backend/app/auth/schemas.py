"""
auth/schemas.py — Schemas Pydantic para autenticação.
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Credenciais de login do usuário."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Resposta com o token JWT gerado após login bem-sucedido."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos até expirar


class TokenPayload(BaseModel):
    """Payload decodificado do JWT."""
    sub: str          # username (sAMAccountName do AD)
    nome: str         # displayName do AD
    exp: int          # timestamp de expiração
    grupos: list[str] = []  # memberOf do AD (opcional)


class UserInfo(BaseModel):
    """Informações do usuário autenticado, retornadas pelo endpoint /auth/me."""
    username: str
    nome: str
    grupos: list[str] = []

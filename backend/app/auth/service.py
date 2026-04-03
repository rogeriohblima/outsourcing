"""
auth/service.py — Serviço de autenticação via Active Directory e geração de JWT.

Fluxo de autenticação:
  1. Usuário envia username + password
  2. Sistema autentica no Active Directory via LDAP (ldap3)
  3. Se autenticado, obtém atributos do usuário (displayName, memberOf)
  4. Gera token JWT assinado com a chave secreta da aplicação
  5. Token é retornado ao cliente e usado nas próximas requisições

Em ambiente de desenvolvimento (APP_ENV=development), se o AD não estiver
acessível, o serviço aceita credenciais de teste locais para facilitar o
desenvolvimento sem dependência de rede.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from ldap3 import ALL_ATTRIBUTES, Connection, Server, SIMPLE, Tls

from app.auth.schemas import TokenPayload, UserInfo
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Usuários de teste para desenvolvimento sem AD
# NUNCA usar em produção
_DEV_USERS: dict[str, dict] = {
    "user": {
        "password": "user",
        "nome": "Usuário Local (Dev)",
        "grupos": ["GRP_SISTEMA_ADMIN"],
    },
    "admin": {
        "password": "admin123",
        "nome": "Administrador (Dev)",
        "grupos": ["GRP_SISTEMA_ADMIN"],
    },
    "fiscal": {
        "password": "fiscal123",
        "nome": "Fiscal (Dev)",
        "grupos": ["GRP_SISTEMA_FISCAL"],
    },
}


# ── Active Directory ──────────────────────────────────────────────────────────

def autenticar_no_ad(username: str, password: str) -> Optional[dict]:
    """
    Autentica o usuário no Active Directory via LDAP bind.

    Retorna um dicionário com atributos do usuário (nome, grupos)
    se a autenticação for bem-sucedida, ou None em caso de falha.

    Args:
        username: sAMAccountName (login de rede do usuário)
        password: senha do usuário

    Returns:
        dict com 'nome' e 'grupos', ou None se falhar
    """
    try:
        # Monta o UPN: usuario@dominio.mil.br
        user_dn = f"{username}@{settings.AD_DOMAIN}"

        tls = Tls(validate=0) if settings.AD_USE_SSL else None
        server = Server(
            settings.AD_SERVER,
            port=settings.AD_PORT,
            use_ssl=settings.AD_USE_SSL,
            tls=tls,
        )

        # Tenta fazer o bind com as credenciais do usuário
        conn = Connection(
            server,
            user=user_dn,
            password=password,
            authentication=SIMPLE,
            raise_exceptions=False,
        )

        if not conn.bind():
            logger.warning(
                "Falha no bind LDAP para usuário '%s': %s",
                username,
                conn.result,
            )
            return None

        # Bind bem-sucedido — busca atributos do usuário
        conn.search(
            search_base=settings.AD_BASE_DN,
            search_filter=f"(sAMAccountName={username})",
            attributes=["displayName", "memberOf"],
        )

        nome = username  # fallback
        grupos: list[str] = []

        if conn.entries:
            entry = conn.entries[0]
            nome = str(entry.displayName) if entry.displayName else username
            if entry.memberOf:
                # Extrai apenas o CN do grupo
                for grupo_dn in entry.memberOf:
                    partes = str(grupo_dn).split(",")
                    cn = partes[0].replace("CN=", "").strip() if partes else ""
                    if cn:
                        grupos.append(cn)

        conn.unbind()
        logger.info("Usuário '%s' autenticado com sucesso no AD.", username)
        return {"nome": nome, "grupos": grupos}

    except Exception as exc:  # noqa: BLE001
        logger.error("Erro ao conectar ao AD: %s", exc)
        return None


def _autenticar_dev(username: str, password: str) -> Optional[dict]:
    """
    Autenticação local para desenvolvimento (sem AD).
    Ativada apenas quando APP_ENV != production.
    """
    user = _DEV_USERS.get(username)
    if user and user["password"] == password:
        logger.debug("Usuário '%s' autenticado via credencial de dev.", username)
        return {"nome": user["nome"], "grupos": user["grupos"]}
    return None


def autenticar_usuario(username: str, password: str) -> Optional[dict]:
    """
    Ponto de entrada principal para autenticação.

    - APP_ENV=production : usa apenas o AD (sem fallback local).
    - APP_ENV=development: pula o AD e usa credenciais locais diretamente,
      evitando o timeout de conexão quando o AD não está acessível.
    - Outros ambientes   : tenta o AD primeiro; se falhar, usa credenciais locais.

    Credenciais de desenvolvimento (nunca usar em produção):
      user  / user       — acesso completo
      admin / admin123   — acesso completo
      fiscal/ fiscal123  — acesso de fiscal
    """
    # Em desenvolvimento, pula o AD completamente para evitar timeout
    if settings.APP_ENV.lower() == "development":
        resultado = _autenticar_dev(username, password)
        if resultado is None:
            logger.warning(
                "Credencial '%s' nao encontrada nos usuarios de dev. "
                "Usuarios disponiveis: %s",
                username, list(_DEV_USERS.keys()),
            )
        return resultado

    # Em produção: somente AD
    if settings.is_production:
        return autenticar_no_ad(username, password)

    # Outros ambientes (testing, staging): tenta AD, fallback local
    resultado = autenticar_no_ad(username, password)
    if resultado is None:
        logger.warning("AD indisponivel — tentando credencial local.")
        resultado = _autenticar_dev(username, password)
    return resultado


# ── JWT ───────────────────────────────────────────────────────────────────────

def criar_token_acesso(username: str, nome: str, grupos: list[str]) -> str:
    """
    Cria um token JWT assinado com os dados do usuário.

    Args:
        username: identificador único do usuário (sAMAccountName)
        nome    : nome de exibição do usuário
        grupos  : lista de grupos do AD

    Returns:
        Token JWT como string
    """
    agora = datetime.now(timezone.utc)
    expira = agora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": username,
        "nome": nome,
        "grupos": grupos,
        "iat": int(agora.timestamp()),
        "exp": int(expira.timestamp()),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> Optional[TokenPayload]:
    """
    Decodifica e valida um token JWT.

    Returns:
        TokenPayload se o token for válido, None caso contrário.
    """
    try:
        dados = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return TokenPayload(**dados)
    except JWTError as exc:
        logger.debug("Token inválido: %s", exc)
        return None


def obter_info_usuario(token: str) -> Optional[UserInfo]:
    """
    Obtém as informações do usuário a partir do token JWT.

    Wrapper de conveniência sobre decodificar_token.
    """
    payload = decodificar_token(token)
    if payload is None:
        return None
    return UserInfo(
        username=payload.sub,
        nome=payload.nome,
        grupos=payload.grupos,
    )
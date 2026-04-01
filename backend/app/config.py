"""
config.py — Configurações da aplicação via variáveis de ambiente.

Utiliza pydantic-settings para leitura e validação automática
das variáveis definidas no arquivo .env.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações globais da aplicação.

    Todas as variáveis são lidas do arquivo .env (ou do ambiente do sistema).
    Valores padrão seguros para desenvolvimento local estão definidos aqui,
    mas devem ser sobrescritos em produção.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Aplicação ────────────────────────────────────────────────────────────
    APP_NAME: str = "Sistema de Contrato de Impressoras"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── Banco de Dados ────────────────────────────────────────────────────────
    # URL assíncrona usada pela aplicação em runtime
    DATABASE_URL: str = "sqlite+aiosqlite:///./contrato_impressoras.db"
    # URL síncrona usada pelo Alembic para migrações
    SYNC_DATABASE_URL: str = "sqlite:///./contrato_impressoras.db"

    # ── JWT ───────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "chave-insegura-para-dev-troque-em-producao"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 horas

    # ── Active Directory ──────────────────────────────────────────────────────
    AD_SERVER: str = "10.10.10.10"
    AD_PORT: int = 389
    AD_USE_SSL: bool = False
    AD_DOMAIN: str = "organizacao.mil.br"
    AD_BASE_DN: str = "DC=organizacao,DC=mil,DC=br"
    AD_BIND_USER: str = ""
    AD_BIND_PASSWORD: str = ""

    # ── SNMP ─────────────────────────────────────────────────────────────────
    SNMP_COMMUNITY: str = "public"
    SNMP_PORT: int = 161
    SNMP_TIMEOUT: int = 5
    SNMP_RETRIES: int = 2

    # ── Upload de Arquivos ────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Aceita string JSON ou lista Python."""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @property
    def is_sqlite(self) -> bool:
        """Retorna True se o banco configurado for SQLite."""
        return "sqlite" in self.DATABASE_URL.lower()

    @property
    def is_production(self) -> bool:
        """Retorna True se o ambiente for produção."""
        return self.APP_ENV.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Retorna a instância singleton das configurações.

    O decorator @lru_cache garante que o arquivo .env seja lido
    apenas uma vez durante o ciclo de vida da aplicação.
    """
    return Settings()

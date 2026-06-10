"""Configuração da aplicação carregada de variáveis de ambiente ou `.env`.

Cada grupo lógico (Telegram, banco, LLM, etc.) é uma sub-classe de
`BaseSettings` com seu próprio prefixo de variável. A classe `Settings`
agrega as sub-settings; callers acessam como `settings.telegram.bot_token`.

Uso em código:

    from chatbot.config import get_settings
    settings = get_settings()
    print(settings.telegram.mode)

Em testes, instanciar as sub-settings diretamente com env vars controladas
via ``monkeypatch.setenv(...)`` — ver ``tests/unit/test_config.py``.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configuração compartilhada por todas as sub-settings.
# `extra="ignore"` evita que variáveis fora do escopo de cada grupo
# (ex.: TELEGRAM_* lidas por DatabaseSettings) causem erro de validação.
_COMMON = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
    case_sensitive=False,
)


TelegramMode = Literal["polling", "webhook"]
LLMProvider = Literal["gemini", "anthropic", "openai", "groq", "ollama"]
EmbeddingProvider = Literal["gemini", "openai", "sentence-transformers"]
LogFormat = Literal["json", "text"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class TelegramSettings(BaseSettings):
    """Configuração do bot do Telegram (prefixo: ``TELEGRAM_``)."""

    model_config = SettingsConfigDict(env_prefix="TELEGRAM_", **_COMMON)

    bot_token: SecretStr = Field(min_length=1)
    mode: TelegramMode = "polling"
    webhook_url: HttpUrl | None = None

    @model_validator(mode="after")
    def _webhook_url_required_when_webhook(self) -> "TelegramSettings":
        if self.mode == "webhook" and self.webhook_url is None:
            raise ValueError("TELEGRAM_WEBHOOK_URL é obrigatório quando TELEGRAM_MODE=webhook")
        return self


class DatabaseSettings(BaseSettings):
    """Configuração do banco (prefixo: ``DATABASE_``).

    ``url`` deve ser uma DSN aceita pelo SQLAlchemy. Exemplo:
    ``postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot``.
    """

    model_config = SettingsConfigDict(env_prefix="DATABASE_", **_COMMON)

    url: str = Field(min_length=1)


class LLMSettings(BaseSettings):
    """Configuração do provedor de LLM (prefixo: ``LLM_``).

    Ver ``docs/03-Integracoes/LLM-Provedores.md`` para o comparativo.
    """

    model_config = SettingsConfigDict(env_prefix="LLM_", **_COMMON)

    provider: LLMProvider = "gemini"
    model: str = "gemini-2.5-flash"
    api_key: SecretStr | None = None


class EmbeddingSettings(BaseSettings):
    """Configuração do provedor de embeddings (prefixo: ``EMBEDDING_``)."""

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_", **_COMMON)

    provider: EmbeddingProvider = "gemini"
    model: str = "text-embedding-004"
    api_key: SecretStr | None = None


class GoogleSettings(BaseSettings):
    """Credenciais Google (prefixo: ``GOOGLE_``).

    Caminhos são relativos à raiz do projeto. Em produção considerar paths
    absolutos ou montagem via secrets manager.
    """

    model_config = SettingsConfigDict(env_prefix="GOOGLE_", **_COMMON)

    oauth_client_secrets_path: str = "./client_secret.json"
    oauth_token_store_path: str = "./.google-tokens/"
    drive_kb_folder_id: str = ""


class SistemaAcademicoSettings(BaseSettings):
    """Configuração do sistema acadêmico (prefixo: ``SISTEMA_ACADEMICO_``).

    Em dev usar ``mock=True`` para repositórios fake
    (``infrastructure/sistema_academico/mock_*``). Em produção,
    ``mock=False`` + ``base_url`` real. Ver
    ``docs/03-Integracoes/Sistema-Academico.md``.
    """

    model_config = SettingsConfigDict(env_prefix="SISTEMA_ACADEMICO_", **_COMMON)

    base_url: str = ""
    api_key: SecretStr | None = None
    mock: bool = False


class ObservabilitySettings(BaseSettings):
    """Configuração de log operacional (prefixo: ``LOG_``).

    Não confundir com o log de *interações* (que é domínio de
    Observabilidade — persistido no banco). Este é o log da aplicação.
    """

    model_config = SettingsConfigDict(env_prefix="LOG_", **_COMMON)

    level: LogLevel = "INFO"
    format: LogFormat = "json"


class Settings:
    """Agregador das sub-settings.

    Cada atributo é uma sub-classe de :class:`BaseSettings` instanciada na
    construção — cada uma lê seu próprio prefixo do mesmo ``.env``.
    """

    def __init__(self) -> None:
        self.telegram: TelegramSettings = TelegramSettings()
        self.database: DatabaseSettings = DatabaseSettings()
        self.llm: LLMSettings = LLMSettings()
        self.embedding: EmbeddingSettings = EmbeddingSettings()
        self.google: GoogleSettings = GoogleSettings()
        self.sistema_academico: SistemaAcademicoSettings = SistemaAcademicoSettings()
        self.observability: ObservabilitySettings = ObservabilitySettings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devolve uma única instância de :class:`Settings` por processo."""
    return Settings()

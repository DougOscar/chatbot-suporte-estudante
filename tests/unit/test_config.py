"""Testes do carregamento de configuração via pydantic-settings.

Isolação de ambiente (chdir + delenv) está em ``tests/unit/conftest.py``.
"""

import pytest
from pydantic import ValidationError

from chatbot.config import (
    DatabaseSettings,
    EmbeddingSettings,
    GoogleSettings,
    LLMSettings,
    ObservabilitySettings,
    Settings,
    SistemaAcademicoSettings,
    TelegramSettings,
    get_settings,
)


class TestTelegramSettings:
    def test_carrega_polling_por_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")

        s = TelegramSettings()

        assert s.bot_token.get_secret_value() == "123:abc"
        assert s.mode == "polling"
        assert s.webhook_url is None

    def test_token_obrigatorio(self) -> None:
        with pytest.raises(ValidationError):
            TelegramSettings()

    def test_token_vazio_rejeitado(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")

        with pytest.raises(ValidationError):
            TelegramSettings()

    def test_webhook_mode_exige_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
        monkeypatch.setenv("TELEGRAM_MODE", "webhook")

        with pytest.raises(ValidationError, match="WEBHOOK_URL"):
            TelegramSettings()

    def test_webhook_mode_com_url_valida(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
        monkeypatch.setenv("TELEGRAM_MODE", "webhook")
        monkeypatch.setenv("TELEGRAM_WEBHOOK_URL", "https://exemplo.com/bot")

        s = TelegramSettings()

        assert s.mode == "webhook"
        assert str(s.webhook_url) == "https://exemplo.com/bot"

    def test_mode_invalido(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
        monkeypatch.setenv("TELEGRAM_MODE", "carrier-pigeon")

        with pytest.raises(ValidationError):
            TelegramSettings()


class TestDatabaseSettings:
    def test_carrega_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        dsn = "postgresql+psycopg://chatbot:senha@localhost:5432/chatbot"
        monkeypatch.setenv("DATABASE_URL", dsn)

        assert DatabaseSettings().url == dsn

    def test_url_obrigatoria(self) -> None:
        with pytest.raises(ValidationError):
            DatabaseSettings()


class TestLLMSettings:
    def test_defaults(self) -> None:
        s = LLMSettings()

        assert s.provider == "gemini"
        assert s.model == "gemini-2.5-flash"
        assert s.api_key is None

    def test_override_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("LLM_MODEL", "claude-haiku-4-5")
        monkeypatch.setenv("LLM_API_KEY", "sk-fake")

        s = LLMSettings()

        assert s.provider == "anthropic"
        assert s.model == "claude-haiku-4-5"
        assert s.api_key is not None
        assert s.api_key.get_secret_value() == "sk-fake"

    def test_provider_invalido(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_PROVIDER", "skynet")

        with pytest.raises(ValidationError):
            LLMSettings()


class TestEmbeddingSettings:
    def test_defaults(self) -> None:
        s = EmbeddingSettings()

        assert s.provider == "gemini"
        assert s.model == "text-embedding-004"
        assert s.api_key is None


class TestGoogleSettings:
    def test_defaults(self) -> None:
        s = GoogleSettings()

        assert s.oauth_client_secrets_path == "./client_secret.json"
        assert s.oauth_token_store_path == "./.google-tokens/"
        assert s.drive_kb_folder_id == ""

    def test_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GOOGLE_DRIVE_KB_FOLDER_ID", "1abc-folder-id")

        assert GoogleSettings().drive_kb_folder_id == "1abc-folder-id"


class TestSistemaAcademicoSettings:
    def test_defaults_aceita_vazios(self) -> None:
        # Placeholder enquanto a API real não existe — não falhar quando vazio.
        s = SistemaAcademicoSettings()

        assert s.base_url == ""
        assert s.api_key is None


class TestObservabilitySettings:
    def test_defaults(self) -> None:
        s = ObservabilitySettings()

        assert s.level == "INFO"
        assert s.format == "json"

    def test_level_invalido(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LOG_LEVEL", "VERBOSE")

        with pytest.raises(ValidationError):
            ObservabilitySettings()


class TestSettingsAggregator:
    def test_compoe_sub_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h/db")
        monkeypatch.setenv("GOOGLE_DRIVE_KB_FOLDER_ID", "folder-x")

        s = Settings()

        assert s.telegram.bot_token.get_secret_value() == "123:abc"
        assert s.database.url == "postgresql+psycopg://u:p@h/db"
        assert s.google.drive_kb_folder_id == "folder-x"
        # Sub-settings opcionais caem em defaults
        assert s.llm.provider == "gemini"
        assert s.observability.level == "INFO"

    def test_get_settings_e_cacheado(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h/db")

        s1 = get_settings()
        s2 = get_settings()

        assert s1 is s2

"""Fixtures compartilhadas para testes unitários.

Unit tests rodam **sem rede, sem banco, sem .env real**. A fixture
`_isolated_env` é autouse: garante que cada teste comece num cwd limpo
(sem ``.env``) e sem variáveis de ambiente do projeto vazadas.

Testes de integração ficam em ``tests/integration/`` e têm seu próprio
``conftest.py``, sem esta isolação.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest

from chatbot.config import get_settings

# Variáveis que as sub-settings do projeto podem ler.
_ENV_VARS = (
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_MODE",
    "TELEGRAM_WEBHOOK_URL",
    "DATABASE_URL",
    "LLM_PROVIDER",
    "LLM_MODEL",
    "LLM_API_KEY",
    "EMBEDDING_PROVIDER",
    "EMBEDDING_MODEL",
    "EMBEDDING_API_KEY",
    "GOOGLE_OAUTH_CLIENT_SECRETS_PATH",
    "GOOGLE_OAUTH_TOKEN_STORE_PATH",
    "GOOGLE_DRIVE_KB_FOLDER_ID",
    "SISTEMA_ACADEMICO_BASE_URL",
    "SISTEMA_ACADEMICO_API_KEY",
    "SISTEMA_ACADEMICO_MOCK",
    "GOOGLE_CALENDAR_MOCK",
    "GOOGLE_CALENDAR_OAUTH_REDIRECT_URI",
    "GOOGLE_CALENDAR_TOKENS_ENCRYPTION_KEY",
    "LOG_LEVEL",
    "LOG_FORMAT",
)


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Isola cada teste unitário de qualquer ``.env`` real ou variável vazada."""
    monkeypatch.chdir(tmp_path)
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

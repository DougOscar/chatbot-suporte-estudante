"""Fixtures para testes de integração.

Diferente dos unit tests, integration tests **usam o ambiente real**
(``.env``) e tocam o banco. Pulam automaticamente se ``DATABASE_URL`` não
estiver disponível (via env do shell ou ``.env`` na raiz).
"""

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from chatbot.config import DatabaseSettings
from chatbot.infrastructure.persistence.engine import create_engine, create_session_factory


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Pula apenas testes marcados como `integration` se DB não estiver configurado.

    Hook em conftest aplica a *todos* os itens da execução; por isso filtramos
    explicitamente pelo marker — sem isso, afetaríamos também unit tests.
    """
    try:
        DatabaseSettings()
    except ValidationError:
        skip = pytest.mark.skip(reason="DATABASE_URL ausente — pulando testes de integração")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    # Usa `DatabaseSettings` direto, não `get_settings()` — assim os testes
    # de integração rodam mesmo sem `TELEGRAM_BOT_TOKEN` etc. configurados.
    eng = create_engine(DatabaseSettings().url)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return create_session_factory(engine)

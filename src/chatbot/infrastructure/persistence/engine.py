"""Engine e session factory async para Postgres + psycopg 3.

Funções são lazy — não criam engine no import. O composition root
(``interfaces/telegram_bot``) chama ``create_engine`` uma única vez na
inicialização e injeta a session factory nos adapters.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from chatbot.config import get_settings


def create_engine(url: str | None = None, *, echo: bool = False) -> AsyncEngine:
    """Cria a engine async. URL vem de ``settings.database.url`` por default."""
    dsn = url or get_settings().database.url
    return create_async_engine(dsn, echo=echo, future=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Devolve uma factory de sessões async ligada à engine."""
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

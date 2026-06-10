"""Ambiente de migração do Alembic (modo async, psycopg 3).

A URL do banco vem de ``DatabaseSettings`` (não do agregador ``Settings``),
para que o Alembic rode mesmo sem o resto do ambiente configurado
(``TELEGRAM_BOT_TOKEN`` etc.). ``DatabaseSettings`` é instanciada *dentro*
das funções de migração para que comandos sem efeitos no banco
(``alembic history``, etc.) não exijam ``DATABASE_URL``.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from chatbot.config import DatabaseSettings
from chatbot.infrastructure.persistence import models  # noqa: F401  (registra os modelos)
from chatbot.infrastructure.persistence.base import Base

# Configuração do alembic.ini
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _aplicar_database_url() -> None:
    """Injeta a DSN real na config do alembic."""
    config.set_main_option("sqlalchemy.url", DatabaseSettings().url)


def run_migrations_offline() -> None:
    """Modo offline: gera SQL sem se conectar ao banco."""
    _aplicar_database_url()
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Modo online: conecta no banco com engine async (psycopg 3)."""
    _aplicar_database_url()
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

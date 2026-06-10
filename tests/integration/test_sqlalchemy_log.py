"""Integração: ``SqlAlchemyInteracaoLog`` contra Postgres real.

Cada teste usa ``telegram_user_id`` aleatório (suficientemente grande) para
não colidir com dados pré-existentes na tabela.
"""

import random
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatbot.domain.observabilidade import Interacao
from chatbot.infrastructure.observabilidade.sqlalchemy_log import SqlAlchemyInteracaoLog
from chatbot.infrastructure.persistence import models

pytestmark = pytest.mark.integration


def _interacao(**override: object) -> Interacao:
    base: dict[str, object] = {
        "aluno_id": None,
        "telegram_user_id": random.randint(10**12, 10**13),
        "chat_id": random.randint(10**12, 10**13),
        "mensagem_recebida": "oi",
        "intencao_detectada": "SAUDACAO",
        "resposta_enviada": "olá!",
        "llm_provider": "none",
        "llm_model": "none",
        "prompt_versao": "test-0",
    }
    base.update(override)
    return Interacao(**base)  # type: ignore[arg-type]


async def test_registrar_persiste_linha(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    adapter = SqlAlchemyInteracaoLog(session_factory)
    interacao = _interacao(
        mensagem_recebida="oi tudo bem?",
        resposta_enviada="oi! tudo sim.",
        tokens_entrada=15,
        tokens_saida=8,
        latencia_ms=420,
    )

    await adapter.registrar(interacao)

    async with session_factory() as session:
        stmt = select(models.Interacao).where(
            models.Interacao.telegram_user_id == interacao.telegram_user_id
        )
        row = (await session.execute(stmt)).scalar_one()

    assert row.mensagem_recebida == "oi tudo bem?"
    assert row.resposta_enviada == "oi! tudo sim."
    assert row.tokens_entrada == 15
    assert row.tokens_saida == 8
    assert row.latencia_ms == 420
    assert row.criado_em is not None  # preenchido pelo server_default
    assert row.contexto_recuperado == {}


async def test_contexto_recuperado_persiste_jsonb(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    adapter = SqlAlchemyInteracaoLog(session_factory)
    ctx = {"chunks": ["abc", "def"], "scores": [0.91, 0.83], "doc_id": "x123"}
    interacao = _interacao(contexto_recuperado=ctx)

    await adapter.registrar(interacao)

    async with session_factory() as session:
        stmt = select(models.Interacao.contexto_recuperado).where(
            models.Interacao.telegram_user_id == interacao.telegram_user_id
        )
        recuperado = (await session.execute(stmt)).scalar_one()

    assert recuperado == ctx


async def test_aluno_id_uuid_persiste(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # Cria um aluno para satisfazer a FK.
    aluno_id = uuid4()
    async with session_factory() as session:
        session.add(models.Aluno(id=aluno_id, telegram_user_id=random.randint(10**12, 10**13)))
        await session.commit()

    adapter = SqlAlchemyInteracaoLog(session_factory)
    interacao = _interacao(aluno_id=aluno_id)

    await adapter.registrar(interacao)

    async with session_factory() as session:
        stmt = select(models.Interacao.aluno_id).where(
            models.Interacao.telegram_user_id == interacao.telegram_user_id
        )
        recuperado = (await session.execute(stmt)).scalar_one()

    assert recuperado == aluno_id


async def test_falha_de_persistencia_nao_levanta(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # Força violação de FK: aluno_id inexistente.
    adapter = SqlAlchemyInteracaoLog(session_factory)
    interacao = _interacao(aluno_id=uuid4())  # não existe na tabela aluno

    # O contrato do port é nunca levantar — vira WARNING no log de app.
    await adapter.registrar(interacao)  # não deve erguer

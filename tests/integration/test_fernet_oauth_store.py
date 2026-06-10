"""Integração de ``FernetOAuthStore``: Fernet + Postgres real."""

import random
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatbot.domain.calendario import OAuthToken
from chatbot.infrastructure.google.calendar.fernet_oauth_store import FernetOAuthStore
from chatbot.infrastructure.persistence import models

pytestmark = pytest.mark.integration


@pytest.fixture
def fernet_key() -> bytes:
    return Fernet.generate_key()


def _telegram_id() -> int:
    return random.randint(10**12, 10**13)


async def test_salvar_e_buscar_round_trip(
    session_factory: async_sessionmaker[AsyncSession], fernet_key: bytes
) -> None:
    store = FernetOAuthStore(session_factory=session_factory, encryption_key=fernet_key)
    tg = _telegram_id()
    expira = datetime.now(UTC) + timedelta(hours=1)
    token = OAuthToken(
        access_token="atoken-secret",
        refresh_token="rtoken-secret",
        expira_em=expira,
    )

    await store.salvar(telegram_user_id=tg, token=token)
    recuperado = await store.buscar(tg)

    assert recuperado is not None
    assert recuperado.access_token == "atoken-secret"
    assert recuperado.refresh_token == "rtoken-secret"
    assert recuperado.expira_em is not None


async def test_tokens_persistem_cifrados_em_repouso(
    session_factory: async_sessionmaker[AsyncSession], fernet_key: bytes
) -> None:
    store = FernetOAuthStore(session_factory=session_factory, encryption_key=fernet_key)
    tg = _telegram_id()
    await store.salvar(
        telegram_user_id=tg,
        token=OAuthToken(access_token="claro-secret-123"),
    )

    # Lê direto da tabela: bytes não devem conter o segredo em texto claro.
    async with session_factory() as session:
        stmt = (
            select(models.OAuthGoogleToken.access_token_cifrado)
            .join(models.Aluno, models.OAuthGoogleToken.aluno_id == models.Aluno.id)
            .where(models.Aluno.telegram_user_id == tg)
        )
        cifrado = (await session.execute(stmt)).scalar_one()

    assert b"claro-secret-123" not in cifrado


async def test_chave_errada_falha_decryption(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    key_correta = Fernet.generate_key()
    key_outra = Fernet.generate_key()
    tg = _telegram_id()

    store_a = FernetOAuthStore(session_factory=session_factory, encryption_key=key_correta)
    await store_a.salvar(telegram_user_id=tg, token=OAuthToken(access_token="x"))

    store_b = FernetOAuthStore(session_factory=session_factory, encryption_key=key_outra)
    from cryptography.fernet import InvalidToken

    with pytest.raises(InvalidToken):
        await store_b.buscar(tg)


async def test_buscar_inexistente_retorna_none(
    session_factory: async_sessionmaker[AsyncSession], fernet_key: bytes
) -> None:
    store = FernetOAuthStore(session_factory=session_factory, encryption_key=fernet_key)
    assert await store.buscar(_telegram_id()) is None


async def test_salvar_re_autoriza_substitui_token(
    session_factory: async_sessionmaker[AsyncSession], fernet_key: bytes
) -> None:
    store = FernetOAuthStore(session_factory=session_factory, encryption_key=fernet_key)
    tg = _telegram_id()

    await store.salvar(telegram_user_id=tg, token=OAuthToken(access_token="v1"))
    await store.salvar(telegram_user_id=tg, token=OAuthToken(access_token="v2"))

    recuperado = await store.buscar(tg)
    assert recuperado is not None
    assert recuperado.access_token == "v2"


async def test_dedup_de_adicao_local(
    session_factory: async_sessionmaker[AsyncSession], fernet_key: bytes
) -> None:
    store = FernetOAuthStore(session_factory=session_factory, encryption_key=fernet_key)
    tg = _telegram_id()
    await store.salvar(telegram_user_id=tg, token=OAuthToken(access_token="x"))

    # Cria um evento real (FK no calendario)
    async with session_factory() as session:
        from chatbot.domain.calendario import Audiencia  # noqa: F401

        evento = models.EventoCalendario(
            titulo=f"test-add-gcal-{uuid4()}",
            inicio=datetime.now(UTC) + timedelta(days=5),
            dia_inteiro=True,
            audiencia="global",
        )
        session.add(evento)
        await session.commit()
        evento_id = evento.id

    # Ainda não registrado.
    assert await store.adicao_existente(telegram_user_id=tg, evento_id=evento_id) is None

    await store.registrar_adicao(
        telegram_user_id=tg, evento_id=evento_id, id_evento_google="gcal-xyz"
    )

    assert await store.adicao_existente(telegram_user_id=tg, evento_id=evento_id) == "gcal-xyz"

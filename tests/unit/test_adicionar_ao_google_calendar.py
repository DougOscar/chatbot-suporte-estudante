"""Testes de ``AdicionarAoGoogleCalendar`` com fakes."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from chatbot.application.calendario import (
    Adicionado,
    AdicionarAoGoogleCalendar,
    EventoInexistente,
    JaAdicionado,
    PrecisaAutorizar,
)
from chatbot.domain.calendario import (
    Audiencia,
    EventoCalendario,
    OAuthToken,
)


class _FakeCalendarioRepo:
    def __init__(self, eventos: dict[UUID, EventoCalendario] | None = None) -> None:
        self._eventos = eventos or {}

    async def proximos_eventos(
        self,
        *,
        horizonte: timedelta,
        audiencias: Sequence[Audiencia],
        limite: int = 20,
    ) -> list[EventoCalendario]:
        return list(self._eventos.values())

    async def buscar_por_id(self, evento_id: UUID) -> EventoCalendario | None:
        return self._eventos.get(evento_id)


class _FakeExterno:
    def __init__(self) -> None:
        self.chamadas: list[tuple[OAuthToken, EventoCalendario]] = []

    async def criar_evento(self, *, token: OAuthToken, evento: EventoCalendario) -> str:
        self.chamadas.append((token, evento))
        return f"gcal-{evento.id}"


class _FakeStore:
    def __init__(
        self,
        *,
        token: OAuthToken | None = None,
        adicoes: dict[tuple[int, UUID], str] | None = None,
    ) -> None:
        self.token = token
        self.adicoes = adicoes or {}

    async def salvar(self, *, telegram_user_id: int, token: OAuthToken) -> None:
        self.token = token

    async def buscar(self, telegram_user_id: int) -> OAuthToken | None:
        return self.token

    async def registrar_adicao(
        self,
        *,
        telegram_user_id: int,
        evento_id: UUID,
        id_evento_google: str,
    ) -> None:
        self.adicoes[(telegram_user_id, evento_id)] = id_evento_google

    async def adicao_existente(self, *, telegram_user_id: int, evento_id: UUID) -> str | None:
        return self.adicoes.get((telegram_user_id, evento_id))


def _evento(evento_id: UUID | None = None) -> EventoCalendario:
    return EventoCalendario(
        id=evento_id or uuid4(),
        titulo="Prova de SO",
        inicio=datetime(2026, 8, 1, tzinfo=UTC),
        audiencia=Audiencia.global_(),
    )


@pytest.fixture
def token_valido() -> OAuthToken:
    return OAuthToken(access_token="mock-access", refresh_token="mock-refresh")


async def test_sem_token_retorna_precisa_autorizar(
    token_valido: OAuthToken,
) -> None:
    evento = _evento()
    uc = AdicionarAoGoogleCalendar(
        repository=_FakeCalendarioRepo({evento.id: evento}),
        externo=_FakeExterno(),
        store=_FakeStore(token=None),
    )

    resultado = await uc(telegram_user_id=1, evento_id=evento.id)

    assert isinstance(resultado, PrecisaAutorizar)


async def test_evento_inexistente_retorna_status(token_valido: OAuthToken) -> None:
    uc = AdicionarAoGoogleCalendar(
        repository=_FakeCalendarioRepo({}),  # vazio
        externo=_FakeExterno(),
        store=_FakeStore(token=token_valido),
    )

    resultado = await uc(telegram_user_id=1, evento_id=uuid4())

    assert isinstance(resultado, EventoInexistente)


async def test_cria_evento_e_registra(token_valido: OAuthToken) -> None:
    evento = _evento()
    externo = _FakeExterno()
    store = _FakeStore(token=token_valido)
    uc = AdicionarAoGoogleCalendar(
        repository=_FakeCalendarioRepo({evento.id: evento}),
        externo=externo,
        store=store,
    )

    resultado = await uc(telegram_user_id=42, evento_id=evento.id)

    assert isinstance(resultado, Adicionado)
    assert resultado.id_evento_google == f"gcal-{evento.id}"
    assert len(externo.chamadas) == 1
    assert (42, evento.id) in store.adicoes


async def test_dedup_local(token_valido: OAuthToken) -> None:
    evento = _evento()
    externo = _FakeExterno()
    store = _FakeStore(
        token=token_valido,
        adicoes={(42, evento.id): "gcal-pre-existente"},
    )
    uc = AdicionarAoGoogleCalendar(
        repository=_FakeCalendarioRepo({evento.id: evento}),
        externo=externo,
        store=store,
    )

    resultado = await uc(telegram_user_id=42, evento_id=evento.id)

    assert isinstance(resultado, JaAdicionado)
    assert resultado.id_evento_google == "gcal-pre-existente"
    # Não chamou a API externa de novo.
    assert externo.chamadas == []

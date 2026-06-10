"""Smoke do ``MockOAuthClient`` + ``MockCalendarAdapter``."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from chatbot.domain.calendario import Audiencia, EventoCalendario, OAuthToken
from chatbot.infrastructure.google.calendar.mock_calendar_adapter import (
    MockCalendarAdapter,
)
from chatbot.infrastructure.google.calendar.mock_oauth_client import MockOAuthClient


class TestMockOAuthClient:
    def test_url_consent_inclui_state(self) -> None:
        client = MockOAuthClient()
        url = client.url_consent(state="42")
        assert "state=42" in url
        assert url.startswith("https://")

    async def test_trocar_code_devolve_token(self) -> None:
        client = MockOAuthClient()
        token = await client.trocar_code("code-de-teste")

        assert "mock-access-" in token.access_token
        assert token.refresh_token is not None
        assert "mock-refresh-" in token.refresh_token
        assert token.expira_em is not None

    async def test_code_vazio_levanta(self) -> None:
        client = MockOAuthClient()
        with pytest.raises(ValueError):
            await client.trocar_code("   ")


class TestMockCalendarAdapter:
    async def test_criar_evento_retorna_id_deterministico(self) -> None:
        adapter = MockCalendarAdapter()
        evento = EventoCalendario(
            id=uuid4(),
            titulo="x",
            inicio=datetime(2026, 8, 1, tzinfo=UTC),
            audiencia=Audiencia.global_(),
        )
        token = OAuthToken(access_token="qualquer")

        id_a = await adapter.criar_evento(token=token, evento=evento)
        id_b = await adapter.criar_evento(token=token, evento=evento)

        assert id_a == id_b
        assert str(evento.id) in id_a

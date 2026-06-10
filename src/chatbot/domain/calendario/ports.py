"""Ports do domínio de Calendário."""

from collections.abc import Sequence
from datetime import timedelta
from typing import Protocol, runtime_checkable
from uuid import UUID

from chatbot.domain.calendario.audiencia import Audiencia
from chatbot.domain.calendario.evento import EventoCalendario
from chatbot.domain.calendario.oauth import OAuthToken


@runtime_checkable
class CalendarioRepository(Protocol):
    """Fonte de verdade do calendário interno."""

    async def proximos_eventos(
        self,
        *,
        horizonte: timedelta,
        audiencias: Sequence[Audiencia],
        limite: int = 20,
    ) -> list[EventoCalendario]:
        """Eventos com ``inicio`` em [agora, agora+horizonte], filtrados por audiência.

        Ordenados por ``inicio`` ascendente. ``audiencias`` é tratado como OR
        (evento entra se seu campo bate com qualquer uma das audiências passadas).
        """
        ...

    async def buscar_por_id(self, evento_id: UUID) -> EventoCalendario | None: ...


@runtime_checkable
class OAuthGoogleStore(Protocol):
    """Persistência cifrada de tokens OAuth Google, indexados por ``telegram_user_id``.

    Adapter padrão: ``infrastructure/google/calendar/fernet_oauth_store.py``
    — Fernet (cryptography) + Postgres. ``salvar`` faz UPSERT do row em
    ``aluno`` (chave natural = telegram_user_id) para criar o aluno virtual.
    """

    async def salvar(self, *, telegram_user_id: int, token: OAuthToken) -> None: ...

    async def buscar(self, telegram_user_id: int) -> OAuthToken | None: ...

    async def registrar_adicao(
        self,
        *,
        telegram_user_id: int,
        evento_id: UUID,
        id_evento_google: str,
    ) -> None:
        """Registra que o aluno adicionou ``evento_id`` ao Google Calendar dele."""
        ...

    async def adicao_existente(self, *, telegram_user_id: int, evento_id: UUID) -> str | None:
        """Retorna ``id_evento_google`` se já existe, senão None (dedup)."""
        ...


@runtime_checkable
class OAuthGoogleClient(Protocol):
    """Gera URL de consent e troca authorization code por token."""

    def url_consent(self, *, state: str) -> str: ...

    async def trocar_code(self, code: str) -> OAuthToken: ...


@runtime_checkable
class CalendarioExterno(Protocol):
    """API do calendário externo do aluno (Google Calendar)."""

    async def criar_evento(self, *, token: OAuthToken, evento: EventoCalendario) -> str:
        """Cria evento no calendário do aluno. Retorna o id externo (Google event id)."""
        ...

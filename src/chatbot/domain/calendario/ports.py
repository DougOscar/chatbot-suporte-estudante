"""Ports do domínio de Calendário."""

from collections.abc import Sequence
from datetime import timedelta
from typing import Protocol, runtime_checkable
from uuid import UUID

from chatbot.domain.calendario.audiencia import Audiencia
from chatbot.domain.calendario.evento import EventoCalendario


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

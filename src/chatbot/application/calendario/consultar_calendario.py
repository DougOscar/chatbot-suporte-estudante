"""Caso de uso ``ConsultarCalendario`` — lê os próximos eventos do banco interno."""

from collections.abc import Sequence
from datetime import timedelta

from chatbot.domain.calendario import Audiencia, CalendarioRepository, EventoCalendario


class ConsultarCalendario:
    def __init__(self, repository: CalendarioRepository) -> None:
        self._repository = repository

    async def __call__(
        self,
        *,
        horizonte: timedelta = timedelta(days=30),
        audiencias: Sequence[Audiencia] | None = None,
    ) -> list[EventoCalendario]:
        if audiencias is None:
            # MVP: sem onboarding aluno↔matrícula, todo alunoo vê apenas
            # eventos globais. Quando Matrícula estiver implementado, o
            # entry point vai derivar as audiências aplicáveis do aluno.
            audiencias = [Audiencia.global_()]
        return await self._repository.proximos_eventos(horizonte=horizonte, audiencias=audiencias)

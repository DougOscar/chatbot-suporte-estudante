"""``AdicionarAoGoogleCalendar`` — adiciona um evento institucional ao
calendário do aluno no Google.

Casos de saída:

- :class:`Adicionado`: criou no Google e registrou localmente.
- :class:`JaAdicionado`: dedup local detectou que o aluno já fez isso.
- :class:`PrecisaAutorizar`: não há token ativo; entry point deve emitir
  URL de consent.
"""

from dataclasses import dataclass
from uuid import UUID

from chatbot.application.calendario.consultar_calendario import ConsultarCalendario
from chatbot.domain.calendario import (
    CalendarioExterno,
    CalendarioRepository,
    OAuthGoogleStore,
)


@dataclass(frozen=True, slots=True)
class Adicionado:
    id_evento_google: str


@dataclass(frozen=True, slots=True)
class JaAdicionado:
    id_evento_google: str


@dataclass(frozen=True, slots=True)
class PrecisaAutorizar:
    pass


@dataclass(frozen=True, slots=True)
class EventoInexistente:
    pass


Resultado = Adicionado | JaAdicionado | PrecisaAutorizar | EventoInexistente


class AdicionarAoGoogleCalendar:
    def __init__(
        self,
        *,
        repository: CalendarioRepository,
        externo: CalendarioExterno,
        store: OAuthGoogleStore,
    ) -> None:
        self._repository = repository
        self._externo = externo
        self._store = store
        # Usado apenas como referência para tipos — não é estritamente
        # necessário. Mantido fora dos campos para evitar dep cíclica
        # com a app layer.
        _ = ConsultarCalendario

    async def __call__(self, *, telegram_user_id: int, evento_id: UUID) -> Resultado:
        ja = await self._store.adicao_existente(
            telegram_user_id=telegram_user_id, evento_id=evento_id
        )
        if ja is not None:
            return JaAdicionado(id_evento_google=ja)

        token = await self._store.buscar(telegram_user_id)
        if token is None:
            return PrecisaAutorizar()

        evento = await self._repository.buscar_por_id(evento_id)
        if evento is None:
            return EventoInexistente()

        id_externo = await self._externo.criar_evento(token=token, evento=evento)

        await self._store.registrar_adicao(
            telegram_user_id=telegram_user_id,
            evento_id=evento_id,
            id_evento_google=id_externo,
        )
        return Adicionado(id_evento_google=id_externo)

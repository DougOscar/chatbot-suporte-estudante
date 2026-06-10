"""Entidade ``EventoCalendario`` — evento institucional do calendário acadêmico."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from chatbot.domain.calendario.audiencia import Audiencia


@dataclass(frozen=True, slots=True, kw_only=True)
class EventoCalendario:
    id: UUID
    titulo: str
    inicio: datetime
    audiencia: Audiencia
    descricao: str | None = None
    fim: datetime | None = None
    dia_inteiro: bool = False
    local: str | None = None

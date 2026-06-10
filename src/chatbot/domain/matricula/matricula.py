"""Entidade ``Matricula`` — vínculo formal do aluno com um curso."""

from dataclasses import dataclass
from datetime import date

from chatbot.domain.matricula.status import StatusMatricula


@dataclass(frozen=True, slots=True, kw_only=True)
class Matricula:
    matricula_id_externo: str
    status: StatusMatricula
    curso: str
    semestre_atual: int
    nome_aluno: str
    desde: date | None = None

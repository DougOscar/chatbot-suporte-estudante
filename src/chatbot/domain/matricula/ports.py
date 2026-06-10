"""Ports do domínio de Matrícula."""

from typing import Protocol, runtime_checkable

from chatbot.domain.matricula.matricula import Matricula


@runtime_checkable
class MatriculaRepository(Protocol):
    """Consulta matrícula do aluno identificado pelo seu ``telegram_user_id``.

    No MVP (sem onboarding), o repositório mock retorna sempre o mesmo aluno
    fictício, independente do telegram_user_id. Quando onboarding for
    implementado, o mapeamento aluno↔telegram será resolvido aqui (ou
    numa camada acima — decisão a tomar).
    """

    async def buscar_por_telegram(self, telegram_user_id: int) -> Matricula | None: ...

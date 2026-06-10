"""Caso de uso ``ConsultarMatricula``."""

from chatbot.domain.matricula import Matricula, MatriculaRepository


class ConsultarMatricula:
    def __init__(self, repository: MatriculaRepository) -> None:
        self._repository = repository

    async def __call__(self, *, telegram_user_id: int) -> Matricula | None:
        return await self._repository.buscar_por_telegram(telegram_user_id)

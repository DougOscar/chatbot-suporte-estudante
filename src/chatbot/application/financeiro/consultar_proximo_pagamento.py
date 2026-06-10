"""Caso de uso ``ConsultarProximoPagamento``."""

from chatbot.domain.financeiro import FinanceiroRepository, Pagamento


class ConsultarProximoPagamento:
    def __init__(self, repository: FinanceiroRepository) -> None:
        self._repository = repository

    async def __call__(self, *, telegram_user_id: int) -> Pagamento | None:
        return await self._repository.proximo_em_aberto(telegram_user_id)

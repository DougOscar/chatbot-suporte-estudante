"""Ports do domínio Financeiro."""

from typing import Protocol, runtime_checkable

from chatbot.domain.financeiro.pagamento import Pagamento


@runtime_checkable
class FinanceiroRepository(Protocol):
    """Consulta pagamentos do aluno (identificação via ``telegram_user_id``).

    Mesma nota de onboarding do ``MatriculaRepository``: no MVP, o mock
    retorna sempre dados de um aluno fictício.
    """

    async def proximo_em_aberto(self, telegram_user_id: int) -> Pagamento | None: ...

    async def listar_pendentes(self, telegram_user_id: int) -> list[Pagamento]: ...

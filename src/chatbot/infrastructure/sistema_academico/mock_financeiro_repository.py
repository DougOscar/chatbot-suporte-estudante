"""Repositório fake de Financeiro para desenvolvimento sem API real.

Devolve dois pagamentos: um em aberto vencendo em ~8 dias, e um pago no
mês anterior (para popular o histórico). Idêntico para qualquer
``telegram_user_id``.
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from chatbot.domain.financeiro import Pagamento, StatusPagamento


def _proximo_em_aberto() -> Pagamento:
    return Pagamento(
        referencia="Mensalidade junho/2026",
        valor=Decimal("890.00"),
        vencimento=date.today() + timedelta(days=8),
        status=StatusPagamento.EM_ABERTO,
        url_boleto="https://portal-aluno.exemplo.edu.br/boletos/2024001234-06-2026.pdf",
    )


def _pago_mes_anterior() -> Pagamento:
    return Pagamento(
        referencia="Mensalidade maio/2026",
        valor=Decimal("890.00"),
        vencimento=date.today() - timedelta(days=22),
        status=StatusPagamento.PAGO,
        pago_em=datetime.now(UTC) - timedelta(days=25),
    )


class MockFinanceiroRepository:
    """Implementa ``FinanceiroRepository`` por duck-typing."""

    async def proximo_em_aberto(self, telegram_user_id: int) -> Pagamento | None:
        return _proximo_em_aberto()

    async def listar_pendentes(self, telegram_user_id: int) -> list[Pagamento]:
        # Por enquanto só 1 pendente (a próxima mensalidade). Dá pra adicionar
        # multas/taxas conforme precisar enriquecer o demo.
        return [_proximo_em_aberto()]

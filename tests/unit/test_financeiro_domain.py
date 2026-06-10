"""Testes do domínio Financeiro."""

from datetime import date
from decimal import Decimal

import pytest

from chatbot.domain.financeiro import Pagamento, StatusPagamento


class TestStatusPagamento:
    def test_valores_canonicos(self) -> None:
        assert StatusPagamento.EM_ABERTO == "EM_ABERTO"
        assert StatusPagamento.PAGO == "PAGO"
        assert StatusPagamento.VENCIDO == "VENCIDO"
        assert StatusPagamento.EM_NEGOCIACAO == "EM_NEGOCIACAO"

    def test_set_completo_bate_com_glossario(self) -> None:
        assert {s.value for s in StatusPagamento} == {
            "EM_ABERTO",
            "PAGO",
            "VENCIDO",
            "EM_NEGOCIACAO",
        }


class TestPagamento:
    def test_instancia_minima(self) -> None:
        p = Pagamento(
            referencia="Mensalidade 06/2026",
            valor=Decimal("890.00"),
            vencimento=date(2026, 6, 15),
            status=StatusPagamento.EM_ABERTO,
        )

        assert p.url_boleto is None
        assert p.pago_em is None

    def test_valor_e_decimal_preciso(self) -> None:
        # Confirma que não há perda de precisão (Decimal vs float).
        p = Pagamento(
            referencia="x",
            valor=Decimal("0.1") + Decimal("0.2"),
            vencimento=date(2026, 6, 15),
            status=StatusPagamento.EM_ABERTO,
        )
        assert p.valor == Decimal("0.3")

    def test_imutavel(self) -> None:
        p = Pagamento(
            referencia="x",
            valor=Decimal("0.00"),
            vencimento=date(2026, 6, 15),
            status=StatusPagamento.EM_ABERTO,
        )
        with pytest.raises(Exception):
            p.referencia = "y"  # type: ignore[misc]

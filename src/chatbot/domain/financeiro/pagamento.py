"""Entidade ``Pagamento`` — uma cobrança específica direcionada ao aluno.

Usa :class:`decimal.Decimal` em ``valor`` para evitar imprecisão de float
em dinheiro.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from chatbot.domain.financeiro.status import StatusPagamento


@dataclass(frozen=True, slots=True, kw_only=True)
class Pagamento:
    referencia: str
    valor: Decimal
    vencimento: date
    status: StatusPagamento
    url_boleto: str | None = None
    pago_em: datetime | None = None

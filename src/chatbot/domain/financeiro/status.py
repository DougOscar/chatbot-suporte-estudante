"""Status canônicos de pagamento. Documentados em
``docs/05-Modelagem/Glossario-Ubiquo.md``."""

from enum import StrEnum


class StatusPagamento(StrEnum):
    EM_ABERTO = "EM_ABERTO"
    PAGO = "PAGO"
    VENCIDO = "VENCIDO"
    EM_NEGOCIACAO = "EM_NEGOCIACAO"

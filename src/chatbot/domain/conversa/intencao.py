"""Enum de intenções classificadas pelo orquestrador de Conversa.

Valores espelham os documentados em ``docs/05-Modelagem/Glossario-Ubiquo.md``.
Por ser ``StrEnum``, os valores serializam direto como string na tabela
``interacao.intencao_detectada``.
"""

from enum import StrEnum


class Intencao(StrEnum):
    SAUDACAO = "SAUDACAO"
    CALENDARIO = "CALENDARIO"
    ADD_GCAL = "ADD_GCAL"
    MATRICULA = "MATRICULA"
    PROXIMO_PAGAMENTO = "PROXIMO_PAGAMENTO"
    PAGAMENTOS_LISTAR = "PAGAMENTOS_LISTAR"
    FAQ = "FAQ"
    INDEFINIDO = "INDEFINIDO"

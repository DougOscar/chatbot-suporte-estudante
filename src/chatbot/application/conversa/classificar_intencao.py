"""Classificação de intenção — Opção A: heurísticas (regex).

Migrar para LLM-driven (Opção B) quando precisão das regras se tornar
insuficiente. Por agora a cobertura é só do que está implementado
(SAUDACAO + CALENDARIO); o resto cai em INDEFINIDO.
"""

import re

from chatbot.domain.conversa import Intencao

# Ordem importa: regras mais específicas primeiro. Em particular,
# PROXIMO_PAGAMENTO vem antes de MATRICULA porque "minha mensalidade"
# poderia disparar MATRICULA por causa de "mensal" → preferimos pagamento.
_REGRAS: list[tuple[re.Pattern[str], Intencao]] = [
    (
        re.compile(
            r"(?i)"
            r"\b(?:pagamento|pagamentos|mensalidade|mensalidades|boleto|boletos|"
            r"cobran[çc]a|cobran[çc]as|vencimento|inadimpl[êe]ncia|inadimplente)\b"
            r"|"
            r"\bquando\s+vence\b"
            r"|"
            r"\bquanto\s+(?:vou\s+pagar|pagar|pago)\b"
        ),
        Intencao.PROXIMO_PAGAMENTO,
    ),
    (
        re.compile(
            r"(?i)"
            r"\b(?:matr[íi]cula|matriculad[oa]|trancad[oa]|trancamento|"
            r"meu\s+curso|meu\s+semestre|situa[çc][ãa]o\s+acad[êe]mica)\b"
        ),
        Intencao.MATRICULA,
    ),
    (
        re.compile(
            r"(?i)"
            r"\b(?:calend[áa]rio|prova|provas|prazo|recesso|datas?|eventos?|aulas?)\b"
            r"|"
            r"pr[óo]xim[oa]s?\s+(?:eventos?|datas?|provas?|aulas?)"
        ),
        Intencao.CALENDARIO,
    ),
    (
        re.compile(r"(?i)^(/start\b|ol[áa]\b|oi\b|bom\s+dia|boa\s+tarde|boa\s+noite)"),
        Intencao.SAUDACAO,
    ),
]


class ClassificarIntencao:
    """Stateless por design — instanciar uma vez no composition root."""

    def __call__(self, texto: str) -> Intencao:
        for padrao, intencao in _REGRAS:
            if padrao.search(texto):
                return intencao
        return Intencao.INDEFINIDO

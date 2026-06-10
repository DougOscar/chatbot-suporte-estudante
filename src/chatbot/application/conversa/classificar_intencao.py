"""Classificação de intenção — Opção A: heurísticas (regex).

Migrar para LLM-driven (Opção B) quando precisão das regras se tornar
insuficiente. Por agora a cobertura é só do que está implementado
(SAUDACAO + CALENDARIO); o resto cai em INDEFINIDO.
"""

import re

from chatbot.domain.conversa import Intencao

_REGRAS: list[tuple[re.Pattern[str], Intencao]] = [
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

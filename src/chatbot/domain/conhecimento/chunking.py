"""Estratégia de chunking — função pura, sem deps externas.

Início: split por linhas em branco (parágrafos) + merge sequencial até
``max_chars``. Sem overlap. Quando a qualidade ficar problemática,
migrar para chunking por header (h1/h2/h3) — ver
``docs/02-Dominios/Conhecimento.md`` para o trade-off.

Estimativa de tokens: ~4 chars/token em pt-BR. Default ``max_chars=2400``
visa ~600 tokens/chunk, dentro do confortável para Gemini embeddings.
"""

import re

_PARAGRAFO = re.compile(r"\n\s*\n")


def chunk_texto(texto: str, *, max_chars: int = 2400) -> list[str]:
    """Divide ``texto`` em chunks de até ``max_chars`` chars cada.

    Tenta preservar limites de parágrafo. Parágrafos individuais maiores
    que ``max_chars`` são cortados na maior fronteira possível.
    """
    if not texto.strip():
        return []

    paragrafos = [p.strip() for p in _PARAGRAFO.split(texto) if p.strip()]

    chunks: list[str] = []
    atual: list[str] = []
    tamanho_atual = 0

    for paragrafo in paragrafos:
        # Parágrafo gigante isolado vai inteiro (mesmo passando do limite)
        # — preferimos limites semânticos a corte arbitrário.
        if len(paragrafo) > max_chars and not atual:
            chunks.append(paragrafo)
            continue

        adicional = len(paragrafo) + (2 if atual else 0)  # +2 do "\n\n"
        if tamanho_atual + adicional > max_chars and atual:
            chunks.append("\n\n".join(atual))
            atual = [paragrafo]
            tamanho_atual = len(paragrafo)
        else:
            atual.append(paragrafo)
            tamanho_atual += adicional

    if atual:
        chunks.append("\n\n".join(atual))

    return chunks

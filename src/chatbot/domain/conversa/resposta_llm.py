"""Resposta normalizada de qualquer provedor de LLM.

Cada adapter (``infrastructure/llm/<provedor>.py``) é responsável por
mapear sua resposta nativa para este formato.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RespostaLLM:
    texto: str
    tokens_entrada: int
    tokens_saida: int
    modelo: str
    provider: str

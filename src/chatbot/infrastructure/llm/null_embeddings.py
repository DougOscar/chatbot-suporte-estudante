"""``EmbeddingGateway`` fallback — retorna vetor zero.

Usado quando ``EMBEDDING_API_KEY`` está vazio. Permite que sync e
busca rodem sem crash, mas a relevância da busca semântica fica
degradada (todos os scores próximos de zero).
"""

from collections.abc import Sequence


class NullEmbeddingsGateway:
    """Vetor zero de tamanho fixo (``EMBEDDING_DIM`` do schema)."""

    def __init__(self, dimensao: int = 768) -> None:
        self._dim = dimensao

    async def embed(self, texto: str) -> list[float]:
        return [0.0] * self._dim

    async def embed_batch(self, textos: Sequence[str]) -> list[list[float]]:
        return [[0.0] * self._dim for _ in textos]

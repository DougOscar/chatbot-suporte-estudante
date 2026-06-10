"""``EmbeddingGateway`` para Google Gemini via ``google-genai``.

Modelo default: ``text-embedding-004`` (768-dim — bate com ``models.EMBEDDING_DIM``).
Trocar o modelo exige nova migração no banco (dimensão da coluna vector).
"""

from collections.abc import Sequence

try:
    from google import genai
except ImportError as _exc:  # pragma: no cover
    raise ImportError("Pacote 'google-genai' não instalado. Rode: uv sync --extra gemini") from _exc


class GeminiEmbeddingsGateway:
    def __init__(self, *, api_key: str, model: str = "text-embedding-004") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def embed(self, texto: str) -> list[float]:
        resultado = await self.embed_batch([texto])
        return resultado[0]

    async def embed_batch(self, textos: Sequence[str]) -> list[list[float]]:
        if not textos:
            return []
        response = await self._client.aio.models.embed_content(
            model=self._model,
            contents=list(textos),
        )
        embeddings = response.embeddings or []
        return [list(e.values or []) for e in embeddings]

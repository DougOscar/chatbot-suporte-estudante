"""``EmbeddingGateway`` para Google Gemini via ``google-genai``.

Modelo default: ``gemini-embedding-001`` com ``output_dimensionality=768`` (bate
com ``models.EMBEDDING_DIM``). Mudar a dimensão exige nova migração no banco.
"""

from collections.abc import Sequence

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError as _exc:  # pragma: no cover
    raise ImportError("Pacote 'google-genai' não instalado. Rode: uv sync --extra gemini") from _exc


class GeminiEmbeddingsGateway:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gemini-embedding-001",
        output_dimensionality: int = 768,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._config = genai_types.EmbedContentConfig(output_dimensionality=output_dimensionality)

    async def embed(self, texto: str) -> list[float]:
        resultado = await self.embed_batch([texto])
        return resultado[0]

    async def embed_batch(self, textos: Sequence[str]) -> list[list[float]]:
        if not textos:
            return []
        response = await self._client.aio.models.embed_content(
            model=self._model,
            contents=list(textos),
            config=self._config,
        )
        embeddings = response.embeddings or []
        return [list(e.values or []) for e in embeddings]

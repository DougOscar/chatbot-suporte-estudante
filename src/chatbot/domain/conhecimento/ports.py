"""Ports do domínio de Conhecimento."""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from chatbot.domain.conhecimento.documento import (
    ChunkKB,
    DocumentoKB,
    ResultadoBusca,
)


@runtime_checkable
class EmbeddingGateway(Protocol):
    """Gera embeddings vetoriais para texto.

    Implementações: Gemini (``text-embedding-004``, 768-dim) ou null
    (vetor zero, fallback sem chave). A dimensão precisa bater com
    ``models.EMBEDDING_DIM``.
    """

    async def embed(self, texto: str) -> list[float]: ...

    async def embed_batch(self, textos: Sequence[str]) -> list[list[float]]: ...


@runtime_checkable
class KbSyncSource(Protocol):
    """Fonte externa de documentos para sincronização (Google Docs, etc.)."""

    async def listar_documentos(self) -> list[DocumentoKB]: ...

    async def carregar_texto(self, documento_id: str) -> str: ...


@runtime_checkable
class KbRepository(Protocol):
    """Persistência local da base de conhecimento (Postgres + pgvector)."""

    async def upsert_documento(self, documento: DocumentoKB) -> None: ...

    async def substituir_chunks(self, documento_id: str, chunks: Sequence[ChunkKB]) -> None:
        """Apaga chunks antigos do documento e insere os novos (atômico)."""
        ...

    async def listar_documentos(self) -> list[DocumentoKB]: ...

    async def remover_documento(self, documento_id: str) -> None:
        """Remove documento + seus chunks (FK cascade)."""
        ...

    async def buscar_por_similaridade(
        self, vetor: Sequence[float], *, top_k: int = 5
    ) -> list[ResultadoBusca]: ...

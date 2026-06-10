"""Entidades do domínio de Conhecimento."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentoKB:
    """Metadados de um documento institucional sincronizado.

    ``id`` é o ``google_doc_id`` da fonte — não inventamos UUID.
    """

    id: str
    titulo: str
    url: str
    atualizado_em_origem: datetime | None = None
    hash_conteudo: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ChunkKB:
    """Pedaço de texto de um :class:`DocumentoKB` com embedding associado.

    ``embedding=None`` é válido para chunks recém-divididos antes de
    passar pelo :class:`EmbeddingGateway`.
    """

    documento_id: str
    indice: int
    texto: str
    embedding: list[float] | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ResultadoBusca:
    """Resultado da busca por similaridade — chunk + documento + score.

    ``score`` em [0, 1] (mais alto = mais relevante). Mantemos o
    ``documento`` para que o LLM possa citar o título/URL na resposta.
    """

    chunk: ChunkKB
    documento: DocumentoKB
    score: float


@dataclass(slots=True, kw_only=True)
class ResumoSincronizacao:
    """Sumário do que aconteceu numa execução do sync.

    Diferente dos value objects do domínio, este é um *accumulator*
    populado durante a execução — por isso não é frozen.
    """

    documentos_processados: int = 0
    documentos_pulados: int = 0
    chunks_inseridos: int = 0
    documentos_removidos: int = 0
    erros: list[str] = field(default_factory=list)

"""Adapter ``KbRepository`` em Postgres + pgvector.

Similaridade via operador ``<=>`` do pgvector (cosine distance). O score
exposto no domínio é ``1 - distance``, ficando em [0, 1] (1 = idêntico).
"""

from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatbot.domain.conhecimento import (
    ChunkKB,
    DocumentoKB,
    ResultadoBusca,
)
from chatbot.infrastructure.persistence import models


class SqlAlchemyKbRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def upsert_documento(self, documento: DocumentoKB) -> None:
        stmt = pg_insert(models.DocumentoKB).values(
            id=documento.id,
            titulo=documento.titulo,
            url=documento.url,
            atualizado_em_origem=documento.atualizado_em_origem,
            hash_conteudo=documento.hash_conteudo,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "titulo": stmt.excluded.titulo,
                "url": stmt.excluded.url,
                "atualizado_em_origem": stmt.excluded.atualizado_em_origem,
                "hash_conteudo": stmt.excluded.hash_conteudo,
            },
        )
        async with self._session_factory() as session:
            await session.execute(stmt)
            await session.commit()

    async def substituir_chunks(self, documento_id: str, chunks: Sequence[ChunkKB]) -> None:
        """Apaga chunks antigos e insere os novos numa única transação."""
        async with self._session_factory() as session:
            await session.execute(
                delete(models.KBChunk).where(models.KBChunk.documento_id == documento_id)
            )
            for chunk in chunks:
                session.add(
                    models.KBChunk(
                        documento_id=chunk.documento_id,
                        indice=chunk.indice,
                        texto=chunk.texto,
                        embedding=chunk.embedding or [],
                    )
                )
            await session.commit()

    async def listar_documentos(self) -> list[DocumentoKB]:
        async with self._session_factory() as session:
            rows = (await session.execute(select(models.DocumentoKB))).scalars().all()
        return [_doc_para_dominio(r) for r in rows]

    async def remover_documento(self, documento_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(models.DocumentoKB).where(models.DocumentoKB.id == documento_id)
            )
            await session.commit()

    async def buscar_por_similaridade(
        self, vetor: Sequence[float], *, top_k: int = 5
    ) -> list[ResultadoBusca]:
        distance = models.KBChunk.embedding.cosine_distance(list(vetor))
        stmt = (
            select(
                models.KBChunk,
                models.DocumentoKB,
                distance.label("distance"),
            )
            .join(
                models.DocumentoKB,
                models.KBChunk.documento_id == models.DocumentoKB.id,
            )
            .order_by(distance)
            .limit(top_k)
        )
        async with self._session_factory() as session:
            rows = (await session.execute(stmt)).all()

        return [
            ResultadoBusca(
                chunk=_chunk_para_dominio(chunk_row),
                documento=_doc_para_dominio(doc_row),
                score=max(0.0, 1.0 - float(dist)),
            )
            for chunk_row, doc_row, dist in rows
        ]


def _doc_para_dominio(row: models.DocumentoKB) -> DocumentoKB:
    return DocumentoKB(
        id=row.id,
        titulo=row.titulo,
        url=row.url,
        atualizado_em_origem=row.atualizado_em_origem,
        hash_conteudo=row.hash_conteudo,
    )


def _chunk_para_dominio(row: models.KBChunk) -> ChunkKB:
    return ChunkKB(
        documento_id=row.documento_id,
        indice=row.indice,
        texto=row.texto,
        embedding=list(row.embedding) if row.embedding is not None else None,
    )

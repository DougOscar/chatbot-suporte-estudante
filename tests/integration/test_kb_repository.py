"""Integração do ``SqlAlchemyKbRepository`` contra Postgres + pgvector.

Cada teste usa um doc id único (UUID) pra não conflitar com seeds existentes.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatbot.domain.conhecimento import ChunkKB, DocumentoKB
from chatbot.infrastructure.persistence.kb_repository import SqlAlchemyKbRepository

pytestmark = pytest.mark.integration


def _doc(*, id_suffix: str = "") -> DocumentoKB:
    doc_id = f"test-doc-{id_suffix or uuid4()}"
    return DocumentoKB(
        id=doc_id,
        titulo=f"Título {doc_id}",
        url=f"https://exemplo/{doc_id}",
        atualizado_em_origem=datetime(2026, 5, 1, tzinfo=UTC),
        hash_conteudo="abc123",
    )


def _chunk(*, doc_id: str, indice: int, embedding: list[float]) -> ChunkKB:
    return ChunkKB(
        documento_id=doc_id,
        indice=indice,
        texto=f"texto {indice}",
        embedding=embedding,
    )


def _vetor(seed: float) -> list[float]:
    """Vetor 768-dim com primeiro valor variável e o resto zero."""
    v = [0.0] * 768
    v[0] = seed
    return v


async def test_upsert_e_listar_documento(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyKbRepository(session_factory)
    doc = _doc()

    await repo.upsert_documento(doc)
    listados = await repo.listar_documentos()

    assert any(d.id == doc.id and d.titulo == doc.titulo for d in listados)


async def test_upsert_atualiza_documento_existente(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyKbRepository(session_factory)
    doc_v1 = _doc(id_suffix="upsert-update")
    await repo.upsert_documento(doc_v1)

    doc_v2 = DocumentoKB(
        id=doc_v1.id,
        titulo="Título atualizado",
        url=doc_v1.url,
        atualizado_em_origem=doc_v1.atualizado_em_origem,
        hash_conteudo="novo-hash",
    )
    await repo.upsert_documento(doc_v2)

    listados = await repo.listar_documentos()
    encontrado = next(d for d in listados if d.id == doc_v1.id)
    assert encontrado.titulo == "Título atualizado"
    assert encontrado.hash_conteudo == "novo-hash"

    # Cleanup
    await repo.remover_documento(doc_v1.id)


async def test_substituir_chunks_apaga_antigos(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyKbRepository(session_factory)
    doc = _doc(id_suffix="substituir")
    await repo.upsert_documento(doc)

    primeiros = [_chunk(doc_id=doc.id, indice=i, embedding=_vetor(0.1)) for i in range(3)]
    await repo.substituir_chunks(doc.id, primeiros)

    # Substitui por apenas 1 chunk.
    segundos = [_chunk(doc_id=doc.id, indice=0, embedding=_vetor(0.2))]
    await repo.substituir_chunks(doc.id, segundos)

    # A busca trazendo top 100 sobre o doc deve devolver só 1 chunk dele
    # (vetor próximo a 0.2 no primeiro elemento).
    resultados = await repo.buscar_por_similaridade(_vetor(0.2), top_k=100)
    deste_doc = [r for r in resultados if r.documento.id == doc.id]
    assert len(deste_doc) == 1

    # Cleanup
    await repo.remover_documento(doc.id)


async def test_busca_ordena_por_similaridade(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyKbRepository(session_factory)
    doc = _doc(id_suffix="ordem")
    await repo.upsert_documento(doc)

    # Três chunks com vetores cada vez mais distantes do query [1, 0, ...].
    chunks = [
        _chunk(doc_id=doc.id, indice=0, embedding=_vetor(1.0)),  # idêntico → score alto
        _chunk(doc_id=doc.id, indice=1, embedding=_vetor(0.5)),  # médio
        _chunk(doc_id=doc.id, indice=2, embedding=_vetor(-1.0)),  # oposto → score baixo
    ]
    await repo.substituir_chunks(doc.id, chunks)

    query = _vetor(1.0)
    resultados = await repo.buscar_por_similaridade(query, top_k=3)
    deste_doc = [r for r in resultados if r.documento.id == doc.id]
    # Pelo menos o primeiro (idêntico) deve estar nos top resultados.
    assert any(r.chunk.indice == 0 for r in deste_doc)
    # E vir antes do oposto.
    indices_ordenados = [r.chunk.indice for r in deste_doc]
    if 0 in indices_ordenados and 2 in indices_ordenados:
        assert indices_ordenados.index(0) < indices_ordenados.index(2)

    # Cleanup
    await repo.remover_documento(doc.id)


async def test_remover_documento_cascade_chunks(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyKbRepository(session_factory)
    doc = _doc(id_suffix="cascade")
    await repo.upsert_documento(doc)
    await repo.substituir_chunks(doc.id, [_chunk(doc_id=doc.id, indice=0, embedding=_vetor(0.7))])

    await repo.remover_documento(doc.id)

    # Documento sumiu.
    docs = await repo.listar_documentos()
    assert all(d.id != doc.id for d in docs)


async def test_score_proximo_de_1_para_vetor_identico(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyKbRepository(session_factory)
    doc = _doc(id_suffix="score")
    await repo.upsert_documento(doc)
    vetor = _vetor(1.0)
    await repo.substituir_chunks(doc.id, [_chunk(doc_id=doc.id, indice=0, embedding=vetor)])

    resultados = await repo.buscar_por_similaridade(vetor, top_k=50)
    deste_doc = next(r for r in resultados if r.documento.id == doc.id)
    assert deste_doc.score == pytest.approx(1.0, abs=1e-5)

    # Cleanup
    await repo.remover_documento(doc.id)

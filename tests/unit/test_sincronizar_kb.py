"""Testes de ``SincronizarKB``."""

from collections.abc import Sequence
from datetime import UTC, datetime

from chatbot.application.conhecimento import SincronizarKB
from chatbot.domain.conhecimento import ChunkKB, DocumentoKB, ResultadoBusca


class _FakeSource:
    def __init__(self) -> None:
        self.docs: dict[str, tuple[DocumentoKB, str]] = {
            "doc-1": (
                DocumentoKB(
                    id="doc-1",
                    titulo="Doc 1",
                    url="https://exemplo/1",
                    atualizado_em_origem=datetime(2026, 5, 1, tzinfo=UTC),
                ),
                "Primeiro parágrafo do doc 1.\n\nSegundo parágrafo do doc 1.",
            ),
            "doc-2": (
                DocumentoKB(id="doc-2", titulo="Doc 2", url="https://exemplo/2"),
                "Conteúdo único do doc 2.",
            ),
        }
        self.erros_carregar: set[str] = set()

    async def listar_documentos(self) -> list[DocumentoKB]:
        return [d for d, _ in self.docs.values()]

    async def carregar_texto(self, documento_id: str) -> str:
        if documento_id in self.erros_carregar:
            raise RuntimeError(f"falha simulada em {documento_id}")
        return self.docs[documento_id][1]


class _FakeRepo:
    def __init__(self) -> None:
        self.docs_upsertados: list[DocumentoKB] = []
        self.chunks_por_doc: dict[str, list[ChunkKB]] = {}

    async def upsert_documento(self, documento: DocumentoKB) -> None:
        self.docs_upsertados.append(documento)

    async def substituir_chunks(self, documento_id: str, chunks: Sequence[ChunkKB]) -> None:
        self.chunks_por_doc[documento_id] = list(chunks)

    async def listar_documentos(self) -> list[DocumentoKB]:
        return []

    async def remover_documento(self, documento_id: str) -> None: ...

    async def buscar_por_similaridade(
        self, vetor: Sequence[float], *, top_k: int = 5
    ) -> list[ResultadoBusca]:
        return []


class _FakeEmbeddings:
    async def embed(self, texto: str) -> list[float]:
        return [0.1] * 768

    async def embed_batch(self, textos: Sequence[str]) -> list[list[float]]:
        return [[0.1] * 768 for _ in textos]


async def test_processa_todos_os_docs_e_insere_chunks() -> None:
    source = _FakeSource()
    repo = _FakeRepo()
    sync = SincronizarKB(source=source, repository=repo, embeddings=_FakeEmbeddings())

    resumo = await sync()

    assert resumo.documentos_processados == 2
    assert resumo.chunks_inseridos >= 2  # ao menos 1 chunk por doc
    assert resumo.erros == []
    assert {d.id for d in repo.docs_upsertados} == {"doc-1", "doc-2"}
    assert set(repo.chunks_por_doc.keys()) == {"doc-1", "doc-2"}


async def test_hash_conteudo_preenchido_no_upsert() -> None:
    source = _FakeSource()
    repo = _FakeRepo()
    sync = SincronizarKB(source=source, repository=repo, embeddings=_FakeEmbeddings())

    await sync()

    for doc in repo.docs_upsertados:
        assert doc.hash_conteudo is not None
        assert len(doc.hash_conteudo) == 64  # SHA-256 hex


async def test_falha_em_um_doc_nao_impede_outros() -> None:
    source = _FakeSource()
    source.erros_carregar = {"doc-1"}
    repo = _FakeRepo()
    sync = SincronizarKB(source=source, repository=repo, embeddings=_FakeEmbeddings())

    resumo = await sync()

    assert resumo.documentos_processados == 1
    assert len(resumo.erros) == 1
    assert "doc-1" in resumo.erros[0]
    assert "doc-2" in {d.id for d in repo.docs_upsertados}


async def test_chunks_indexados_em_ordem() -> None:
    source = _FakeSource()
    # Doc com vários parágrafos pra forçar múltiplos chunks com max_chars baixo.
    source.docs["doc-1"] = (
        source.docs["doc-1"][0],
        "a" * 100 + "\n\n" + "b" * 100 + "\n\n" + "c" * 100,
    )
    repo = _FakeRepo()
    sync = SincronizarKB(
        source=source,
        repository=repo,
        embeddings=_FakeEmbeddings(),
        max_chars_por_chunk=120,
    )

    await sync()

    chunks = repo.chunks_por_doc["doc-1"]
    indices = [c.indice for c in chunks]
    assert indices == sorted(indices)
    assert indices[0] == 0

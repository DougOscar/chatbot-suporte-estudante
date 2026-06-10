"""Testes do caso de uso ``BuscarConhecimento``."""

from collections.abc import Sequence

from chatbot.application.conhecimento import BuscarConhecimento
from chatbot.domain.conhecimento import ChunkKB, DocumentoKB, ResultadoBusca


class _FakeRepo:
    def __init__(self) -> None:
        self.chamadas: list[dict[str, object]] = []
        self.retornar: list[ResultadoBusca] = []

    async def upsert_documento(self, documento: DocumentoKB) -> None: ...

    async def substituir_chunks(self, documento_id: str, chunks: Sequence[ChunkKB]) -> None: ...

    async def listar_documentos(self) -> list[DocumentoKB]:
        return []

    async def remover_documento(self, documento_id: str) -> None: ...

    async def buscar_por_similaridade(
        self, vetor: Sequence[float], *, top_k: int = 5
    ) -> list[ResultadoBusca]:
        self.chamadas.append({"vetor": list(vetor), "top_k": top_k})
        return self.retornar


class _FakeEmbeddings:
    def __init__(self) -> None:
        self.chamadas: list[str] = []

    async def embed(self, texto: str) -> list[float]:
        self.chamadas.append(texto)
        return [0.5, 0.5, 0.5]

    async def embed_batch(self, textos: Sequence[str]) -> list[list[float]]:
        return [[0.5, 0.5, 0.5] for _ in textos]


async def test_embeda_a_pergunta_e_chama_repo_com_o_vetor() -> None:
    repo = _FakeRepo()
    emb = _FakeEmbeddings()
    uc = BuscarConhecimento(repository=repo, embeddings=emb)

    await uc(pergunta="como faço trancamento?")

    assert emb.chamadas == ["como faço trancamento?"]
    assert repo.chamadas[0]["vetor"] == [0.5, 0.5, 0.5]
    assert repo.chamadas[0]["top_k"] == 5


async def test_top_k_customizado() -> None:
    repo = _FakeRepo()
    emb = _FakeEmbeddings()
    uc = BuscarConhecimento(repository=repo, embeddings=emb)

    await uc(pergunta="x", top_k=3)

    assert repo.chamadas[0]["top_k"] == 3


async def test_retorna_resultados_do_repo() -> None:
    repo = _FakeRepo()
    repo.retornar = [
        ResultadoBusca(
            chunk=ChunkKB(documento_id="d1", indice=0, texto="t"),
            documento=DocumentoKB(id="d1", titulo="T", url="u"),
            score=0.9,
        ),
    ]
    uc = BuscarConhecimento(repository=repo, embeddings=_FakeEmbeddings())

    resultados = await uc(pergunta="x")

    assert resultados == repo.retornar

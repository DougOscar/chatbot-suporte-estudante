"""Smoke do mock KB source + null embeddings."""

from chatbot.infrastructure.google.docs.mock_kb_source import MockKbSource
from chatbot.infrastructure.llm.null_embeddings import NullEmbeddingsGateway


class TestMockKbSource:
    async def test_lista_4_documentos(self) -> None:
        source = MockKbSource()
        docs = await source.listar_documentos()
        assert len(docs) == 4
        assert all(d.id.startswith("mock-doc-") for d in docs)
        assert all(d.url.startswith("https://") for d in docs)

    async def test_carrega_texto_de_doc_existente(self) -> None:
        source = MockKbSource()
        docs = await source.listar_documentos()
        texto = await source.carregar_texto(docs[0].id)
        assert len(texto) > 0
        # Conteúdo varia, mas todos têm pelo menos 200 chars úteis.
        assert len(texto.strip()) > 200

    async def test_carregar_doc_inexistente_levanta(self) -> None:
        source = MockKbSource()
        import pytest

        with pytest.raises(KeyError):
            await source.carregar_texto("não-existe")


class TestNullEmbeddings:
    async def test_embed_retorna_vetor_zero_de_768(self) -> None:
        gw = NullEmbeddingsGateway()
        vetor = await gw.embed("qualquer texto")
        assert vetor == [0.0] * 768

    async def test_embed_batch_preserva_quantidade(self) -> None:
        gw = NullEmbeddingsGateway()
        vetores = await gw.embed_batch(["a", "b", "c"])
        assert len(vetores) == 3
        assert all(v == [0.0] * 768 for v in vetores)

    async def test_dimensao_customizada(self) -> None:
        gw = NullEmbeddingsGateway(dimensao=1536)
        vetor = await gw.embed("x")
        assert len(vetor) == 1536

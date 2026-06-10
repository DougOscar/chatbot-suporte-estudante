"""Caso de uso ``BuscarConhecimento`` — RAG durante a conversa.

Embeda a pergunta + busca top-k chunks por similaridade. O LLM
recebe os chunks como contexto e formata a resposta com citação.
"""

from chatbot.domain.conhecimento import EmbeddingGateway, KbRepository, ResultadoBusca


class BuscarConhecimento:
    def __init__(self, *, repository: KbRepository, embeddings: EmbeddingGateway) -> None:
        self._repository = repository
        self._embeddings = embeddings

    async def __call__(self, *, pergunta: str, top_k: int = 5) -> list[ResultadoBusca]:
        vetor = await self._embeddings.embed(pergunta)
        return await self._repository.buscar_por_similaridade(vetor, top_k=top_k)

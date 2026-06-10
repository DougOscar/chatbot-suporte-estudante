"""Ports do domínio de Conversa."""

from typing import Protocol, runtime_checkable

from chatbot.domain.conversa.resposta_llm import RespostaLLM


@runtime_checkable
class LLMGateway(Protocol):
    """Abstração sobre o provedor de LLM.

    Recebe instruções de sistema (persona + contexto) + mensagem do usuário,
    devolve texto gerado com contagem de tokens normalizada.
    """

    async def gerar(
        self,
        *,
        sistema: str,
        usuario: str,
        max_tokens: int = 500,
    ) -> RespostaLLM: ...

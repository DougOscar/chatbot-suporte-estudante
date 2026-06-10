"""Fallback ``LLMGateway`` quando o provedor não está configurado.

Usado em dev/MVP quando ``LLM_API_KEY`` está vazio — permite que o bot
suba e que outros caminhos (calendário, etc.) sejam testados sem
custo nem dependência de provedor externo.
"""

from chatbot.domain.conversa import RespostaLLM


class NullLLMGateway:
    """Devolve uma resposta canned com 0 tokens. Não faz I/O."""

    _MSG = (
        "Ainda não tenho um provedor de LLM configurado, então não consigo "
        "responder em texto natural. Tente perguntas curtas e diretas — "
        "para calendário, por exemplo: 'quais as próximas datas?'."
    )

    async def gerar(
        self,
        *,
        sistema: str,
        usuario: str,
        max_tokens: int = 500,
    ) -> RespostaLLM:
        return RespostaLLM(
            texto=self._MSG,
            tokens_entrada=0,
            tokens_saida=0,
            modelo="null",
            provider="null",
        )

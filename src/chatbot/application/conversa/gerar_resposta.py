"""Caso de uso ``GerarResposta`` — monta prompt + chama LLMGateway.

A montagem do prompt (sistema = persona + contexto serializado em JSON)
fica aqui. O gateway apenas executa a chamada e normaliza tokens.
"""

import json
from typing import Any

from chatbot.domain.conversa import Intencao, LLMGateway, Persona, RespostaLLM


class GerarResposta:
    def __init__(self, gateway: LLMGateway, persona: Persona) -> None:
        self._gateway = gateway
        self._persona = persona

    async def __call__(
        self,
        *,
        intencao: Intencao,
        contexto: dict[str, Any],
        mensagem_usuario: str,
        max_tokens: int = 500,
    ) -> RespostaLLM:
        sistema = self._montar_sistema(intencao=intencao, contexto=contexto)
        return await self._gateway.gerar(
            sistema=sistema, usuario=mensagem_usuario, max_tokens=max_tokens
        )

    def _montar_sistema(self, *, intencao: Intencao, contexto: dict[str, Any]) -> str:
        contexto_serializado = json.dumps(contexto, ensure_ascii=False, default=str)
        return (
            f"{self._persona.instrucoes_sistema}\n"
            f"\n"
            f"[INTENCAO_DETECTADA]\n{intencao.value}\n"
            f"\n"
            f"[CONTEXTO]\n{contexto_serializado}\n"
        )

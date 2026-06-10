"""Adapter ``LLMGateway`` para Google Gemini via SDK ``google-genai``.

Requer a extra ``gemini`` instalada::

    uv sync --extra gemini

Sem ela, importar este módulo levanta ``ImportError`` com instrução clara.
"""

from chatbot.domain.conversa import RespostaLLM

try:
    from google import genai
    from google.genai import types
except ImportError as _exc:  # pragma: no cover
    raise ImportError("Pacote 'google-genai' não instalado. Rode: uv sync --extra gemini") from _exc


class GeminiLLMGateway:
    def __init__(self, *, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def gerar(
        self,
        *,
        sistema: str,
        usuario: str,
        max_tokens: int = 500,
    ) -> RespostaLLM:
        config = types.GenerateContentConfig(
            system_instruction=sistema,
            max_output_tokens=max_tokens,
            temperature=0.4,
        )
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=usuario,
            config=config,
        )

        # Gemini retorna usage_metadata com prompt_token_count + candidates_token_count.
        # Em casos raros (filtros de safety) `text` ou os contadores podem ser None.
        usage = response.usage_metadata
        return RespostaLLM(
            texto=response.text or "",
            tokens_entrada=(usage.prompt_token_count or 0) if usage else 0,
            tokens_saida=(usage.candidates_token_count or 0) if usage else 0,
            modelo=self._model,
            provider="gemini",
        )

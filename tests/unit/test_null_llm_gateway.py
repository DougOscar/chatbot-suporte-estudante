"""Smoke do ``NullLLMGateway`` — fallback usado quando não há chave de LLM."""

from chatbot.infrastructure.llm.null_gateway import NullLLMGateway


async def test_retorna_resposta_padrao_com_zero_tokens() -> None:
    gw = NullLLMGateway()

    r = await gw.gerar(sistema="x", usuario="y")

    assert r.tokens_entrada == 0
    assert r.tokens_saida == 0
    assert r.provider == "null"
    assert r.modelo == "null"
    assert len(r.texto) > 0

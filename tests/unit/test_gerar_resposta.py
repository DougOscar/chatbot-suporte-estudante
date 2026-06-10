"""Testes do caso de uso ``GerarResposta`` com fake gateway."""

import json

from chatbot.application.conversa import GerarResposta
from chatbot.domain.conversa import PERSONA_PADRAO, Intencao, Persona, RespostaLLM


class _FakeGateway:
    def __init__(self) -> None:
        self.chamadas: list[dict[str, object]] = []
        self.responder: RespostaLLM = RespostaLLM(
            texto="ok", tokens_entrada=1, tokens_saida=2, modelo="m", provider="p"
        )

    async def gerar(self, *, sistema: str, usuario: str, max_tokens: int = 500) -> RespostaLLM:
        self.chamadas.append({"sistema": sistema, "usuario": usuario, "max_tokens": max_tokens})
        return self.responder


async def test_chama_gateway_com_persona_e_contexto() -> None:
    gw = _FakeGateway()
    uc = GerarResposta(gateway=gw, persona=PERSONA_PADRAO)

    resposta = await uc(
        intencao=Intencao.CALENDARIO,
        contexto={"eventos": [{"titulo": "X"}]},
        mensagem_usuario="quais as datas?",
    )

    chamada = gw.chamadas[0]
    sistema = chamada["sistema"]
    assert isinstance(sistema, str)
    assert PERSONA_PADRAO.instrucoes_sistema in sistema
    assert "CALENDARIO" in sistema
    assert "[CONTEXTO]" in sistema
    assert "X" in sistema  # contexto serializado
    assert chamada["usuario"] == "quais as datas?"
    assert resposta is gw.responder


async def test_contexto_serializado_em_json() -> None:
    gw = _FakeGateway()
    uc = GerarResposta(gateway=gw, persona=PERSONA_PADRAO)

    await uc(
        intencao=Intencao.CALENDARIO,
        contexto={"acentuação": "ç", "n": 42},
        mensagem_usuario="oi",
    )

    sistema = gw.chamadas[0]["sistema"]
    assert isinstance(sistema, str)
    # ensure_ascii=False — caracteres pt-BR não viram \uXXXX.
    assert "ç" in sistema
    # JSON válido (vai conter as chaves intactas)
    assert '"n": 42' in sistema
    # Garantia ainda mais forte: extraí o bloco e parseio.
    _, _, bloco_ctx = sistema.partition("[CONTEXTO]\n")
    payload = bloco_ctx.strip()
    parsed = json.loads(payload)
    assert parsed == {"acentuação": "ç", "n": 42}


async def test_max_tokens_repassado() -> None:
    gw = _FakeGateway()
    uc = GerarResposta(gateway=gw, persona=PERSONA_PADRAO)

    await uc(
        intencao=Intencao.INDEFINIDO,
        contexto={},
        mensagem_usuario="x",
        max_tokens=123,
    )

    assert gw.chamadas[0]["max_tokens"] == 123


async def test_contexto_com_objetos_nao_json_padrao() -> None:
    # `default=str` no json.dumps cobre datetimes, UUIDs etc.
    from datetime import UTC, datetime
    from uuid import UUID

    gw = _FakeGateway()
    uc = GerarResposta(gateway=gw, persona=PERSONA_PADRAO)

    await uc(
        intencao=Intencao.CALENDARIO,
        contexto={
            "id": UUID("00000000-0000-0000-0000-000000000001"),
            "data": datetime(2026, 6, 15, tzinfo=UTC),
        },
        mensagem_usuario="x",
    )

    sistema = gw.chamadas[0]["sistema"]
    assert isinstance(sistema, str)
    assert "00000000-0000-0000-0000-000000000001" in sistema
    assert "2026-06-15" in sistema


async def test_persona_customizada() -> None:
    gw = _FakeGateway()
    persona_custom = Persona(versao="test-1", instrucoes_sistema="VOCÊ É UM ASSISTENTE DE TESTE")
    uc = GerarResposta(gateway=gw, persona=persona_custom)

    await uc(intencao=Intencao.INDEFINIDO, contexto={}, mensagem_usuario="x")

    assert "VOCÊ É UM ASSISTENTE DE TESTE" in str(gw.chamadas[0]["sistema"])

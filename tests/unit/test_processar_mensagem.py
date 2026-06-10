"""Testes do orquestrador ``ProcessarMensagem``."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from chatbot.application.calendario import ConsultarCalendario
from chatbot.application.conversa import (
    ClassificarIntencao,
    GerarResposta,
    ProcessarMensagem,
)
from chatbot.application.observabilidade import RegistrarInteracao
from chatbot.domain.calendario import Audiencia, EventoCalendario
from chatbot.domain.conversa import PERSONA_PADRAO, RespostaLLM
from chatbot.domain.observabilidade import Interacao


class _FakeRepoCalendario:
    def __init__(self) -> None:
        self.eventos: list[EventoCalendario] = []

    async def proximos_eventos(
        self,
        *,
        horizonte: timedelta,
        audiencias: Sequence[Audiencia],
        limite: int = 20,
    ) -> list[EventoCalendario]:
        return self.eventos

    async def buscar_por_id(self, evento_id: UUID) -> EventoCalendario | None:
        return None


class _FakeGateway:
    def __init__(self) -> None:
        self.deve_levantar: Exception | None = None
        self.responder = RespostaLLM(
            texto="resposta-gerada",
            tokens_entrada=42,
            tokens_saida=17,
            modelo="m-test",
            provider="fake",
        )
        self.chamadas: list[dict[str, Any]] = []

    async def gerar(self, *, sistema: str, usuario: str, max_tokens: int = 500) -> RespostaLLM:
        self.chamadas.append({"sistema": sistema, "usuario": usuario})
        if self.deve_levantar:
            raise self.deve_levantar
        return self.responder


class _FakeLog:
    def __init__(self) -> None:
        self.registradas: list[Interacao] = []

    async def registrar(self, interacao: Interacao) -> None:
        self.registradas.append(interacao)


def _evento(titulo: str) -> EventoCalendario:
    return EventoCalendario(
        id=uuid4(),
        titulo=titulo,
        inicio=datetime(2026, 8, 1, tzinfo=UTC),
        audiencia=Audiencia.global_(),
    )


@dataclass
class _Fakes:
    repo_cal: _FakeRepoCalendario
    gateway: _FakeGateway
    log: _FakeLog
    registrar: RegistrarInteracao
    uc: ProcessarMensagem


@pytest.fixture
def fakes() -> _Fakes:
    repo_cal = _FakeRepoCalendario()
    gateway = _FakeGateway()
    log = _FakeLog()
    registrar = RegistrarInteracao(log)
    uc = ProcessarMensagem(
        classificar=ClassificarIntencao(),
        consultar_calendario=ConsultarCalendario(repo_cal),
        gerar_resposta=GerarResposta(gateway=gateway, persona=PERSONA_PADRAO),
        registrar_interacao=registrar,
        persona=PERSONA_PADRAO,
    )
    return _Fakes(repo_cal=repo_cal, gateway=gateway, log=log, registrar=registrar, uc=uc)


async def test_intencao_calendario_consulta_eventos_e_inclui_no_contexto(
    fakes: _Fakes,
) -> None:
    fakes.repo_cal.eventos = [_evento("Prova X"), _evento("Recesso Y")]

    resposta = await fakes.uc(telegram_user_id=123, chat_id=456, texto="quais as datas?")

    assert resposta == "resposta-gerada"
    sistema = fakes.gateway.chamadas[0]["sistema"]
    assert isinstance(sistema, str)
    assert "Prova X" in sistema
    assert "Recesso Y" in sistema
    assert "CALENDARIO" in sistema


async def test_interacao_logada_com_tokens_e_provider(fakes: _Fakes) -> None:
    await fakes.uc(telegram_user_id=10, chat_id=20, texto="olá")

    await fakes.registrar.aguardar_pendentes()
    log_records = fakes.log.registradas
    assert len(log_records) == 1
    r = log_records[0]
    assert r.telegram_user_id == 10
    assert r.chat_id == 20
    assert r.intencao_detectada == "SAUDACAO"
    assert r.resposta_enviada == "resposta-gerada"
    assert r.tokens_entrada == 42
    assert r.tokens_saida == 17
    assert r.llm_provider == "fake"
    assert r.llm_model == "m-test"
    assert r.prompt_versao == PERSONA_PADRAO.versao
    assert r.erro is None


async def test_intencao_indefinida_nao_consulta_calendario(fakes: _Fakes) -> None:
    fakes.repo_cal.eventos = [_evento("não-deveria-aparecer")]

    await fakes.uc(telegram_user_id=1, chat_id=1, texto="qualquer coisa aleatória")

    sistema = fakes.gateway.chamadas[0]["sistema"]
    assert isinstance(sistema, str)
    assert "não-deveria-aparecer" not in sistema
    assert "INDEFINIDO" in sistema


async def test_falha_no_gateway_loga_erro_e_responde_fallback(fakes: _Fakes) -> None:
    fakes.gateway.deve_levantar = RuntimeError("rate limit estourou")

    resposta = await fakes.uc(telegram_user_id=1, chat_id=1, texto="olá")

    assert "problema" in resposta.lower()
    await fakes.registrar.aguardar_pendentes()
    r = fakes.log.registradas[0]
    assert r.erro == "rate limit estourou"
    assert r.tokens_entrada == 0
    assert r.tokens_saida == 0
    assert r.llm_provider == "none"


async def test_falha_no_repo_calendario_tambem_degrada(fakes: _Fakes) -> None:
    class _RepoQuebrado:
        async def proximos_eventos(self, **_: Any) -> list[EventoCalendario]:
            raise RuntimeError("db down")

        async def buscar_por_id(self, _: UUID) -> None:
            return None

    # Substitui o use case de calendário in-place por um que falha.
    fakes.uc._consultar_calendario = ConsultarCalendario(_RepoQuebrado())

    resposta = await fakes.uc(telegram_user_id=1, chat_id=1, texto="quais as próximas datas?")

    assert "problema" in resposta.lower()
    await fakes.registrar.aguardar_pendentes()
    r = fakes.log.registradas[0]
    assert r.intencao_detectada == "CALENDARIO"
    assert r.erro == "db down"


async def test_resposta_vazia_do_llm_cai_no_fallback(fakes: _Fakes) -> None:
    fakes.gateway.responder = RespostaLLM(
        texto="", tokens_entrada=10, tokens_saida=0, modelo="m", provider="fake"
    )

    resposta = await fakes.uc(telegram_user_id=1, chat_id=1, texto="oi")

    assert resposta != ""
    assert "problema" in resposta.lower()


async def test_persona_versao_grava_no_log(fakes: _Fakes) -> None:
    await fakes.uc(telegram_user_id=1, chat_id=1, texto="oi")
    await fakes.registrar.aguardar_pendentes()
    assert fakes.log.registradas[0].prompt_versao == PERSONA_PADRAO.versao


async def test_contexto_recuperado_grava_no_log(fakes: _Fakes) -> None:
    fakes.repo_cal.eventos = [_evento("Evento A")]
    await fakes.uc(telegram_user_id=1, chat_id=1, texto="calendário")
    await fakes.registrar.aguardar_pendentes()
    ctx = fakes.log.registradas[0].contexto_recuperado
    assert "eventos" in ctx
    assert ctx["eventos"][0]["titulo"] == "Evento A"


async def test_latencia_ms_positiva(fakes: _Fakes) -> None:
    # Substitui `gateway.gerar` por uma versão lenta para garantir latência > 0.
    original = fakes.gateway.gerar

    async def lento(*, sistema: str, usuario: str, max_tokens: int = 500) -> RespostaLLM:
        await asyncio.sleep(0.01)
        return await original(sistema=sistema, usuario=usuario, max_tokens=max_tokens)

    fakes.gateway.gerar = lento  # type: ignore[method-assign]

    await fakes.uc(telegram_user_id=1, chat_id=1, texto="oi")
    await fakes.registrar.aguardar_pendentes()
    assert fakes.log.registradas[0].latencia_ms > 0

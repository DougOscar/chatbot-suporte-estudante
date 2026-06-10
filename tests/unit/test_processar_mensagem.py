"""Testes do orquestrador ``ProcessarMensagem``."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest

from chatbot.application.calendario import ConsultarCalendario
from chatbot.application.conversa import (
    ClassificarIntencao,
    GerarResposta,
    ProcessarMensagem,
)
from chatbot.application.financeiro import ConsultarProximoPagamento
from chatbot.application.matricula import ConsultarMatricula
from chatbot.application.observabilidade import RegistrarInteracao
from chatbot.domain.calendario import Audiencia, EventoCalendario
from chatbot.domain.conversa import PERSONA_PADRAO, RespostaLLM
from chatbot.domain.financeiro import Pagamento, StatusPagamento
from chatbot.domain.matricula import Matricula, StatusMatricula
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


class _FakeMatriculaRepo:
    def __init__(self) -> None:
        self.retornar: Matricula | None = Matricula(
            matricula_id_externo="2024001234",
            status=StatusMatricula.ATIVA,
            curso="ADS",
            semestre_atual=5,
            nome_aluno="Aluno Teste",
            desde=date(2022, 2, 15),
        )

    async def buscar_por_telegram(self, telegram_user_id: int) -> Matricula | None:
        return self.retornar


class _FakeFinanceiroRepo:
    def __init__(self) -> None:
        self.proximo: Pagamento | None = Pagamento(
            referencia="Mensalidade 06/2026",
            valor=Decimal("890.00"),
            vencimento=date(2026, 6, 18),
            status=StatusPagamento.EM_ABERTO,
            url_boleto="https://exemplo.com/boleto.pdf",
        )

    async def proximo_em_aberto(self, telegram_user_id: int) -> Pagamento | None:
        return self.proximo

    async def listar_pendentes(self, telegram_user_id: int) -> list[Pagamento]:
        return [self.proximo] if self.proximo else []


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
    repo_matr: _FakeMatriculaRepo
    repo_fin: _FakeFinanceiroRepo
    gateway: _FakeGateway
    log: _FakeLog
    registrar: RegistrarInteracao
    uc: ProcessarMensagem


@pytest.fixture
def fakes() -> _Fakes:
    repo_cal = _FakeRepoCalendario()
    repo_matr = _FakeMatriculaRepo()
    repo_fin = _FakeFinanceiroRepo()
    gateway = _FakeGateway()
    log = _FakeLog()
    registrar = RegistrarInteracao(log)
    uc = ProcessarMensagem(
        classificar=ClassificarIntencao(),
        consultar_calendario=ConsultarCalendario(repo_cal),
        consultar_matricula=ConsultarMatricula(repo_matr),
        consultar_proximo_pagamento=ConsultarProximoPagamento(repo_fin),
        gerar_resposta=GerarResposta(gateway=gateway, persona=PERSONA_PADRAO),
        registrar_interacao=registrar,
        persona=PERSONA_PADRAO,
    )
    return _Fakes(
        repo_cal=repo_cal,
        repo_matr=repo_matr,
        repo_fin=repo_fin,
        gateway=gateway,
        log=log,
        registrar=registrar,
        uc=uc,
    )


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


async def test_intencao_matricula_inclui_dados_no_contexto(fakes: _Fakes) -> None:
    await fakes.uc(telegram_user_id=1, chat_id=1, texto="qual minha matrícula?")

    sistema = fakes.gateway.chamadas[0]["sistema"]
    assert isinstance(sistema, str)
    assert "MATRICULA" in sistema
    assert "2024001234" in sistema
    assert "ATIVA" in sistema
    assert "Aluno Teste" in sistema


async def test_intencao_matricula_sem_aluno_passa_none_no_contexto(
    fakes: _Fakes,
) -> None:
    fakes.repo_matr.retornar = None

    await fakes.uc(telegram_user_id=1, chat_id=1, texto="qual minha matrícula?")
    await fakes.registrar.aguardar_pendentes()

    ctx = fakes.log.registradas[0].contexto_recuperado
    assert ctx == {"matricula": None}


async def test_intencao_proximo_pagamento_inclui_dados_no_contexto(
    fakes: _Fakes,
) -> None:
    await fakes.uc(telegram_user_id=1, chat_id=1, texto="quando vence minha mensalidade?")

    sistema = fakes.gateway.chamadas[0]["sistema"]
    assert isinstance(sistema, str)
    assert "PROXIMO_PAGAMENTO" in sistema
    assert "890.00" in sistema  # Decimal serializado via default=str
    assert "EM_ABERTO" in sistema
    assert "https://exemplo.com/boleto.pdf" in sistema


async def test_intencao_proximo_pagamento_sem_pagamento_passa_none(
    fakes: _Fakes,
) -> None:
    fakes.repo_fin.proximo = None

    await fakes.uc(telegram_user_id=1, chat_id=1, texto="quando vence?")
    await fakes.registrar.aguardar_pendentes()

    ctx = fakes.log.registradas[0].contexto_recuperado
    assert ctx == {"pagamento": None}


async def test_pagamento_nao_consulta_matricula_nem_calendario(
    fakes: _Fakes,
) -> None:
    fakes.repo_cal.eventos = [_evento("nao-deveria-aparecer")]
    fakes.repo_matr.retornar = Matricula(
        matricula_id_externo="x",
        status=StatusMatricula.ATIVA,
        curso="x",
        semestre_atual=1,
        nome_aluno="OUTRO ALUNO",
    )

    await fakes.uc(telegram_user_id=1, chat_id=1, texto="quando vence?")

    sistema = fakes.gateway.chamadas[0]["sistema"]
    assert isinstance(sistema, str)
    assert "nao-deveria-aparecer" not in sistema
    assert "OUTRO ALUNO" not in sistema

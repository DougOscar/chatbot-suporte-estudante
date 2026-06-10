"""Testes unitários do caso de uso ``RegistrarInteracao``.

O caso de uso é fire-and-forget: agenda persistência em background via
:func:`asyncio.create_task`. Os testes verificam que (a) a chamada não
bloqueia, (b) o port é chamado com o payload correto, (c) ``aguardar_pendentes``
espera as tasks terminarem.
"""

import asyncio

import pytest

from chatbot.application.observabilidade import RegistrarInteracao
from chatbot.domain.observabilidade import Interacao


class _FakeInteracaoLog:
    """Fake do port `InteracaoLog`."""

    def __init__(self, delay_segundos: float = 0.0) -> None:
        self.delay = delay_segundos
        self.registradas: list[Interacao] = []

    async def registrar(self, interacao: Interacao) -> None:
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        self.registradas.append(interacao)


def _interacao_exemplo(**override: object) -> Interacao:
    base: dict[str, object] = {
        "aluno_id": None,
        "telegram_user_id": 42,
        "chat_id": 100,
        "mensagem_recebida": "oi",
        "intencao_detectada": "SAUDACAO",
        "resposta_enviada": "olá!",
        "llm_provider": "none",
        "llm_model": "none",
        "prompt_versao": "test-0",
    }
    base.update(override)
    return Interacao(**base)  # type: ignore[arg-type]


async def test_agenda_em_background_e_persiste() -> None:
    log = _FakeInteracaoLog()
    uc = RegistrarInteracao(log)

    uc(_interacao_exemplo())

    # Ainda não terminou — o agendamento é assíncrono.
    assert log.registradas == []

    await uc.aguardar_pendentes()

    assert len(log.registradas) == 1
    assert log.registradas[0].telegram_user_id == 42


async def test_chamada_nao_bloqueia_quando_log_e_lento() -> None:
    log = _FakeInteracaoLog(delay_segundos=0.5)
    uc = RegistrarInteracao(log)

    inicio = asyncio.get_event_loop().time()
    uc(_interacao_exemplo())
    decorrido = asyncio.get_event_loop().time() - inicio

    # A chamada __call__ é sync e retorna imediatamente.
    assert decorrido < 0.1
    assert log.registradas == []  # ainda não finalizou

    await uc.aguardar_pendentes()
    assert len(log.registradas) == 1


async def test_multiplos_registros_em_paralelo() -> None:
    log = _FakeInteracaoLog()
    uc = RegistrarInteracao(log)

    for i in range(5):
        uc(_interacao_exemplo(telegram_user_id=i))

    await uc.aguardar_pendentes()

    assert {r.telegram_user_id for r in log.registradas} == {0, 1, 2, 3, 4}


async def test_aguardar_pendentes_sem_tarefas_retorna_imediatamente() -> None:
    log = _FakeInteracaoLog()
    uc = RegistrarInteracao(log)

    await uc.aguardar_pendentes()  # não deve travar nem levantar


async def test_excecao_no_log_nao_propaga_para_aguardar_pendentes() -> None:
    class _LogQueLevanta:
        async def registrar(self, interacao: Interacao) -> None:
            raise RuntimeError("falha proposital")

    uc = RegistrarInteracao(_LogQueLevanta())
    uc(_interacao_exemplo())

    # `aguardar_pendentes` usa return_exceptions=True — não propaga.
    # (Em produção, o adapter já encapsula a exceção; este teste cobre
    # o caso defensivo de um port que viole o contrato.)
    await uc.aguardar_pendentes()


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_call_sem_event_loop_levanta_runtime_error() -> None:
    # `asyncio.create_task` exige loop rodando — chamar de contexto sync puro falha.
    # filterwarnings: a corrotina criada por `log.registrar(...)` fica sem await
    # neste caminho de erro — comportamento esperado, warning é cosmético.
    log = _FakeInteracaoLog()
    uc = RegistrarInteracao(log)

    with pytest.raises(RuntimeError):
        uc(_interacao_exemplo())

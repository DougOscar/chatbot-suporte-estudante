"""Testes do classificador de intenção por regex."""

import pytest

from chatbot.application.conversa import ClassificarIntencao
from chatbot.domain.conversa import Intencao


@pytest.fixture
def classificar() -> ClassificarIntencao:
    return ClassificarIntencao()


@pytest.mark.parametrize(
    "texto",
    [
        "qual é o calendário?",
        "calendario",
        "Quais são as próximas datas?",
        "tem alguma próxima prova?",
        "próximos eventos da turma",
        "quando é o prazo da matrícula?",
        "tem recesso semana que vem?",
        "PROVA",
    ],
)
def test_classifica_calendario(classificar: ClassificarIntencao, texto: str) -> None:
    assert classificar(texto) == Intencao.CALENDARIO


@pytest.mark.parametrize(
    "texto",
    [
        "olá",
        "Olá!",
        "oi",
        "Bom dia",
        "boa tarde",
        "Boa noite",
        "/start",
    ],
)
def test_classifica_saudacao(classificar: ClassificarIntencao, texto: str) -> None:
    assert classificar(texto) == Intencao.SAUDACAO


@pytest.mark.parametrize(
    "texto",
    [
        "qualquer outra pergunta aleatória",
        "asdfgh",
        "",
        "obrigado",
    ],
)
def test_indefinido_quando_nenhuma_regra_casa(classificar: ClassificarIntencao, texto: str) -> None:
    assert classificar(texto) == Intencao.INDEFINIDO


def test_calendario_tem_precedencia_sobre_saudacao(
    classificar: ClassificarIntencao,
) -> None:
    # "olá, qual o calendário?" — embora bata em ambas, calendário deve ganhar
    # (regra mais específica vem primeiro na lista).
    assert classificar("olá, qual o calendário?") == Intencao.CALENDARIO

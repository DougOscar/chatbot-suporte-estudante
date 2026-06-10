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
        "qual o prazo final?",
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


@pytest.mark.parametrize(
    "texto",
    [
        "qual minha matrícula?",
        "estou matriculado?",
        "minha situação acadêmica",
        "qual meu curso?",
        "estou trancado?",
        "como faço trancamento?",
        "qual meu semestre atual?",
    ],
)
def test_classifica_matricula(classificar: ClassificarIntencao, texto: str) -> None:
    assert classificar(texto) == Intencao.MATRICULA


@pytest.mark.parametrize(
    "texto",
    [
        "quando vence minha mensalidade?",
        "qual o valor do meu boleto?",
        "tem pagamento em aberto?",
        "estou inadimplente?",
        "quanto vou pagar este mês?",
        "MENSALIDADE",
        "quero ver minhas cobranças",
    ],
)
def test_classifica_proximo_pagamento(classificar: ClassificarIntencao, texto: str) -> None:
    assert classificar(texto) == Intencao.PROXIMO_PAGAMENTO


def test_pagamento_tem_precedencia_sobre_matricula(
    classificar: ClassificarIntencao,
) -> None:
    # "minha mensalidade vence quando?" — ambíguo entre PAGAMENTO e MATRICULA.
    # Regra mais específica (pagamento, primeira na lista) ganha.
    assert classificar("minha mensalidade da matrícula vence quando?") == Intencao.PROXIMO_PAGAMENTO

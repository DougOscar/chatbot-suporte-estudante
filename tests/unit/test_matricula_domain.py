"""Testes do domínio de Matrícula."""

from datetime import date

import pytest

from chatbot.domain.matricula import Matricula, StatusMatricula


class TestStatusMatricula:
    def test_valores_canonicos(self) -> None:
        assert StatusMatricula.ATIVA == "ATIVA"
        assert StatusMatricula.TRANCADA == "TRANCADA"
        assert StatusMatricula.CANCELADA == "CANCELADA"
        assert StatusMatricula.FORMADO == "FORMADO"
        assert StatusMatricula.INADIMPLENTE == "INADIMPLENTE"

    def test_set_completo_bate_com_glossario(self) -> None:
        assert {s.value for s in StatusMatricula} == {
            "ATIVA",
            "TRANCADA",
            "CANCELADA",
            "FORMADO",
            "INADIMPLENTE",
        }


class TestMatricula:
    def test_instancia_minima(self) -> None:
        m = Matricula(
            matricula_id_externo="2024001234",
            status=StatusMatricula.ATIVA,
            curso="ADS",
            semestre_atual=5,
            nome_aluno="Fulano",
        )

        assert m.desde is None
        assert m.status == StatusMatricula.ATIVA

    def test_imutavel(self) -> None:
        m = Matricula(
            matricula_id_externo="x",
            status=StatusMatricula.ATIVA,
            curso="x",
            semestre_atual=1,
            nome_aluno="x",
        )
        with pytest.raises(Exception):
            m.semestre_atual = 6  # type: ignore[misc]

    def test_com_desde(self) -> None:
        m = Matricula(
            matricula_id_externo="x",
            status=StatusMatricula.ATIVA,
            curso="x",
            semestre_atual=1,
            nome_aluno="x",
            desde=date(2022, 2, 15),
        )
        assert m.desde == date(2022, 2, 15)

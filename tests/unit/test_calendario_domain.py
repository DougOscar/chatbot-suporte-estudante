"""Testes do domínio de Calendário (entidade + value object)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from chatbot.domain.calendario import Audiencia, EventoCalendario


class TestAudiencia:
    def test_global_sem_valor(self) -> None:
        a = Audiencia.global_()

        assert a.escopo == "global"
        assert a.valor is None
        assert str(a) == "global"

    def test_global_com_valor_levanta(self) -> None:
        with pytest.raises(ValueError, match="global"):
            Audiencia(escopo="global", valor="foo")

    def test_escopo_nao_global_exige_valor(self) -> None:
        with pytest.raises(ValueError, match="curso"):
            Audiencia(escopo="curso", valor=None)
        with pytest.raises(ValueError, match="curso"):
            Audiencia(escopo="curso", valor="")

    @pytest.mark.parametrize(
        ("raw", "escopo", "valor"),
        [
            ("global", "global", None),
            ("curso:ADM", "curso", "ADM"),
            ("semestre:5", "semestre", "5"),
            ("turma:ADM-5A", "turma", "ADM-5A"),
        ],
    )
    def test_parse(self, raw: str, escopo: str, valor: str | None) -> None:
        a = Audiencia.parse(raw)

        assert a.escopo == escopo
        assert a.valor == valor

    def test_parse_escopo_desconhecido(self) -> None:
        with pytest.raises(ValueError, match="escopo desconhecido"):
            Audiencia.parse("xyz:foo")

    def test_parse_sem_colon_nao_e_global(self) -> None:
        with pytest.raises(ValueError, match="faltou ':'"):
            Audiencia.parse("curso")

    @pytest.mark.parametrize(
        "raw", ["global", "curso:ADM", "semestre:5", "turma:ADM-5A", "curso:foo-bar"]
    )
    def test_roundtrip_parse_str(self, raw: str) -> None:
        assert str(Audiencia.parse(raw)) == raw

    def test_hashable_e_igualdade(self) -> None:
        a = Audiencia.parse("curso:ADM")
        b = Audiencia.parse("curso:ADM")

        assert a == b
        assert hash(a) == hash(b)
        assert {a, b} == {a}  # dedup em set


class TestEventoCalendario:
    def test_instancia_minima(self) -> None:
        ev = EventoCalendario(
            id=uuid4(),
            titulo="Início do semestre",
            inicio=datetime(2026, 8, 1, tzinfo=UTC),
            audiencia=Audiencia.global_(),
        )

        assert ev.descricao is None
        assert ev.fim is None
        assert ev.dia_inteiro is False
        assert ev.local is None

    def test_imutavel(self) -> None:
        ev = EventoCalendario(
            id=uuid4(),
            titulo="X",
            inicio=datetime(2026, 8, 1, tzinfo=UTC),
            audiencia=Audiencia.global_(),
        )

        with pytest.raises(Exception):
            ev.titulo = "Y"  # type: ignore[misc]

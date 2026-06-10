"""Testes do caso de uso ``ConsultarCalendario``."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from chatbot.application.calendario import ConsultarCalendario
from chatbot.domain.calendario import Audiencia, EventoCalendario


class _FakeRepo:
    def __init__(self) -> None:
        self.chamadas: list[dict[str, object]] = []
        self.retornar: list[EventoCalendario] = []

    async def proximos_eventos(
        self,
        *,
        horizonte: timedelta,
        audiencias: Sequence[Audiencia],
        limite: int = 20,
    ) -> list[EventoCalendario]:
        self.chamadas.append(
            {"horizonte": horizonte, "audiencias": list(audiencias), "limite": limite}
        )
        return self.retornar

    async def buscar_por_id(self, evento_id: UUID) -> EventoCalendario | None:
        return None


def _evento() -> EventoCalendario:
    return EventoCalendario(
        id=uuid4(),
        titulo="X",
        inicio=datetime(2026, 8, 1, tzinfo=UTC),
        audiencia=Audiencia.global_(),
    )


async def test_default_usa_horizonte_30_dias_e_audiencia_global() -> None:
    repo = _FakeRepo()
    uc = ConsultarCalendario(repo)

    await uc()

    assert repo.chamadas[0]["horizonte"] == timedelta(days=30)
    assert repo.chamadas[0]["audiencias"] == [Audiencia.global_()]


async def test_audiencias_customizadas_sao_repassadas() -> None:
    repo = _FakeRepo()
    uc = ConsultarCalendario(repo)
    audiencias = [Audiencia.parse("curso:ADM"), Audiencia.parse("semestre:5")]

    await uc(audiencias=audiencias)

    assert repo.chamadas[0]["audiencias"] == audiencias


async def test_horizonte_customizado() -> None:
    repo = _FakeRepo()
    uc = ConsultarCalendario(repo)

    await uc(horizonte=timedelta(days=7))

    assert repo.chamadas[0]["horizonte"] == timedelta(days=7)


async def test_retorna_lista_do_repositorio() -> None:
    repo = _FakeRepo()
    repo.retornar = [_evento(), _evento()]
    uc = ConsultarCalendario(repo)

    eventos = await uc()

    assert eventos == repo.retornar

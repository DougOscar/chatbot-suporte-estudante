"""Integração: ``SqlAlchemyCalendarioRepository`` contra Postgres real.

Cada teste cria eventos com títulos únicos (UUID embutido) para não
interferir com seeds existentes.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatbot.domain.calendario import Audiencia
from chatbot.infrastructure.persistence import models
from chatbot.infrastructure.persistence.calendario_repository import (
    SqlAlchemyCalendarioRepository,
)

pytestmark = pytest.mark.integration


async def _criar_evento(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    titulo_suffix: str,
    dias: int,
    audiencia: str = "global",
) -> str:
    titulo = f"test-evento-{titulo_suffix}-{uuid4()}"
    async with session_factory() as session:
        session.add(
            models.EventoCalendario(
                titulo=titulo,
                inicio=datetime.now(UTC) + timedelta(days=dias),
                dia_inteiro=True,
                audiencia=audiencia,
            )
        )
        await session.commit()
    return titulo


async def test_filtra_por_horizonte(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyCalendarioRepository(session_factory)
    dentro = await _criar_evento(session_factory, titulo_suffix="dentro", dias=5)
    fora = await _criar_evento(session_factory, titulo_suffix="fora", dias=40)

    resultado = await repo.proximos_eventos(
        horizonte=timedelta(days=30),
        audiencias=[Audiencia.global_()],
    )
    titulos = {e.titulo for e in resultado}

    assert dentro in titulos
    assert fora not in titulos


async def test_filtra_por_audiencia(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyCalendarioRepository(session_factory)
    titulo_global = await _criar_evento(
        session_factory, titulo_suffix="g", dias=3, audiencia="global"
    )
    titulo_curso = await _criar_evento(
        session_factory, titulo_suffix="c", dias=3, audiencia="curso:ADM"
    )

    # Apenas global: vê só o global.
    resultado_g = await repo.proximos_eventos(
        horizonte=timedelta(days=30),
        audiencias=[Audiencia.global_()],
    )
    titulos_g = {e.titulo for e in resultado_g}
    assert titulo_global in titulos_g
    assert titulo_curso not in titulos_g

    # Curso:ADM (sem global): vê só o do curso.
    resultado_c = await repo.proximos_eventos(
        horizonte=timedelta(days=30),
        audiencias=[Audiencia.parse("curso:ADM")],
    )
    titulos_c = {e.titulo for e in resultado_c}
    assert titulo_global not in titulos_c
    assert titulo_curso in titulos_c

    # Múltiplas audiências (OR): vê os dois.
    resultado_ambos = await repo.proximos_eventos(
        horizonte=timedelta(days=30),
        audiencias=[Audiencia.global_(), Audiencia.parse("curso:ADM")],
    )
    titulos_ambos = {e.titulo for e in resultado_ambos}
    assert titulo_global in titulos_ambos
    assert titulo_curso in titulos_ambos


async def test_ordena_por_inicio_ascendente(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyCalendarioRepository(session_factory)
    cedo = await _criar_evento(session_factory, titulo_suffix="cedo", dias=2)
    tarde = await _criar_evento(session_factory, titulo_suffix="tarde", dias=10)

    resultado = await repo.proximos_eventos(
        horizonte=timedelta(days=30),
        audiencias=[Audiencia.global_()],
    )

    titulos = [e.titulo for e in resultado]
    assert titulos.index(cedo) < titulos.index(tarde)


async def test_eventos_no_passado_sao_ignorados(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyCalendarioRepository(session_factory)
    passado = await _criar_evento(session_factory, titulo_suffix="passado", dias=-10)

    resultado = await repo.proximos_eventos(
        horizonte=timedelta(days=30),
        audiencias=[Audiencia.global_()],
    )

    assert passado not in {e.titulo for e in resultado}


async def test_buscar_por_id_existente(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyCalendarioRepository(session_factory)
    titulo = await _criar_evento(session_factory, titulo_suffix="byid", dias=5)
    # Recupera o ID via título único
    async with session_factory() as session:
        from sqlalchemy import select

        stmt = select(models.EventoCalendario.id).where(models.EventoCalendario.titulo == titulo)
        evento_id = (await session.execute(stmt)).scalar_one()

    evento = await repo.buscar_por_id(evento_id)

    assert evento is not None
    assert evento.titulo == titulo
    assert evento.audiencia == Audiencia.global_()


async def test_buscar_por_id_inexistente_retorna_none(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyCalendarioRepository(session_factory)

    evento = await repo.buscar_por_id(uuid4())

    assert evento is None


async def test_dominio_mapeia_audiencia_corretamente(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    repo = SqlAlchemyCalendarioRepository(session_factory)
    await _criar_evento(session_factory, titulo_suffix="aud", dias=5, audiencia="curso:CC")

    resultado = await repo.proximos_eventos(
        horizonte=timedelta(days=30),
        audiencias=[Audiencia.parse("curso:CC")],
    )
    aud = next(e for e in resultado if e.audiencia.escopo == "curso").audiencia

    assert aud == Audiencia(escopo="curso", valor="CC")

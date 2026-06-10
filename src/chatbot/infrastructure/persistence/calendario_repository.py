"""Adapter SQLAlchemy do port :class:`CalendarioRepository`."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatbot.domain.calendario import Audiencia, EventoCalendario
from chatbot.infrastructure.persistence import models


class SqlAlchemyCalendarioRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def proximos_eventos(
        self,
        *,
        horizonte: timedelta,
        audiencias: Sequence[Audiencia],
        limite: int = 20,
    ) -> list[EventoCalendario]:
        agora = datetime.now(UTC)
        teto = agora + horizonte
        audiencia_strs = [str(a) for a in audiencias]

        async with self._session_factory() as session:
            stmt = (
                select(models.EventoCalendario)
                .where(
                    models.EventoCalendario.inicio >= agora,
                    models.EventoCalendario.inicio <= teto,
                    models.EventoCalendario.audiencia.in_(audiencia_strs),
                )
                .order_by(models.EventoCalendario.inicio)
                .limit(limite)
            )
            rows = (await session.execute(stmt)).scalars().all()

        return [_para_dominio(r) for r in rows]

    async def buscar_por_id(self, evento_id: UUID) -> EventoCalendario | None:
        async with self._session_factory() as session:
            row = await session.get(models.EventoCalendario, evento_id)
        return _para_dominio(row) if row else None


def _para_dominio(row: models.EventoCalendario) -> EventoCalendario:
    return EventoCalendario(
        id=row.id,
        titulo=row.titulo,
        descricao=row.descricao,
        inicio=row.inicio,
        fim=row.fim,
        dia_inteiro=row.dia_inteiro,
        audiencia=Audiencia.parse(row.audiencia),
        local=row.local,
    )

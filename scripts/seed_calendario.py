"""Popula ``evento_calendario`` com ~15 eventos de exemplo.

Idempotente — cada evento é identificado pelo título; já existe → pula.
Para forçar reinserção: ``TRUNCATE evento_calendario CASCADE;`` antes.

Rodar::

    uv run python scripts/seed_calendario.py
"""

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from chatbot.config import DatabaseSettings
from chatbot.infrastructure.persistence import models
from chatbot.infrastructure.persistence.engine import create_engine, create_session_factory

# Hoje às 9h UTC — base para os offsets.
_HOJE_09H = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)


# (titulo, descricao, dias_a_partir_de_hoje, audiencia)
_EVENTOS: list[tuple[str, str, int, str]] = [
    ("Início do semestre letivo", "Aulas começam para todos os cursos.", 1, "global"),
    ("Semana de boas-vindas", "Workshops e atividades para calouros.", 3, "global"),
    (
        "Prazo final para matrícula em disciplinas",
        "Após esta data não é possível alterar matrícula.",
        7,
        "global",
    ),
    ("Prova bimestral — Análise de Sistemas", "Sala 302, 14h.", 14, "curso:ADM"),
    (
        "Apresentação de TCC — Ciência da Computação",
        "Auditório principal, período da manhã.",
        18,
        "curso:CC",
    ),
    (
        "Visita técnica à empresa parceira",
        "Inscrições limitadas, falar com a coordenação.",
        20,
        "semestre:5",
    ),
    ("Workshop de carreiras", "Palestras com ex-alunos e empresas parceiras.", 22, "global"),
    ("Recesso — feriado municipal", "Sem aulas neste dia.", 25, "global"),
    (
        "Entrega do projeto final — Engenharia de Software",
        "Submeter via portal até as 23:59.",
        28,
        "curso:ES",
    ),
    ("Provas de meio de semestre", "Semana de provas concentradas.", 35, "global"),
    ("Semana acadêmica", "Cinco dias de palestras e mesas-redondas.", 45, "global"),
    (
        "Período de avaliação institucional",
        "Responda o formulário enviado pelo e-mail institucional.",
        50,
        "global",
    ),
    ("Início das férias", "Recesso letivo de inverno.", 60, "global"),
    ("Vestibular de meio de ano", "Inscrições abertas — divulgue.", 65, "global"),
    ("Volta às aulas", "Início do 2º semestre letivo.", 90, "global"),
]


async def _seed() -> tuple[int, int]:
    engine = create_engine(DatabaseSettings().url)
    factory = create_session_factory(engine)

    inseridos = 0
    pulados = 0

    try:
        async with factory() as session:
            for titulo, descricao, dias, audiencia in _EVENTOS:
                ja_existe = await session.execute(
                    select(models.EventoCalendario.id).where(
                        models.EventoCalendario.titulo == titulo
                    )
                )
                if ja_existe.scalar_one_or_none() is not None:
                    pulados += 1
                    continue

                session.add(
                    models.EventoCalendario(
                        titulo=titulo,
                        descricao=descricao,
                        inicio=_HOJE_09H + timedelta(days=dias),
                        dia_inteiro=True,
                        audiencia=audiencia,
                    )
                )
                inseridos += 1

            await session.commit()
    finally:
        await engine.dispose()

    return inseridos, pulados


def main() -> None:
    inseridos, pulados = asyncio.run(_seed())
    print(f"Eventos inseridos: {inseridos} | já existiam: {pulados}")


if __name__ == "__main__":
    main()

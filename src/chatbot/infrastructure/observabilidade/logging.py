"""Configuração de logs estruturados via structlog.

JSON em produção (``LOG_FORMAT=json``); console colorido em dev (``=text``).
Este é o log **operacional** da aplicação — não confundir com o log de
*interações* (que vai para a tabela ``interacao``).
"""

import logging
import sys
from typing import Any

import structlog

from chatbot.config import ObservabilitySettings


def configurar_logging(settings: ObservabilitySettings) -> None:
    nivel = getattr(logging, settings.level)

    processadores_comuns: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    renderer: Any
    if settings.format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*processadores_comuns, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(nivel),
        logger_factory=structlog.WriteLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

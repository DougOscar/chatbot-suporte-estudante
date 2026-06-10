"""Status canônicos de matrícula. Valores documentados em
``docs/05-Modelagem/Glossario-Ubiquo.md``."""

from enum import StrEnum


class StatusMatricula(StrEnum):
    ATIVA = "ATIVA"
    TRANCADA = "TRANCADA"
    CANCELADA = "CANCELADA"
    FORMADO = "FORMADO"
    INADIMPLENTE = "INADIMPLENTE"

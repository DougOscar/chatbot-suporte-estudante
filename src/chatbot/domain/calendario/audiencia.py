"""Value object ``Audiencia`` — para quem um evento se aplica.

Formato canônico em string (mesmo que é armazenado na coluna
``evento_calendario.audiencia``):

- ``global`` — todos os alunos
- ``curso:<sigla>`` — ex.: ``curso:ADM``
- ``semestre:<N>`` — ex.: ``semestre:5``
- ``turma:<id>`` — ex.: ``turma:ADM-5A``
"""

from dataclasses import dataclass
from typing import Literal, cast

EscopoAudiencia = Literal["global", "curso", "semestre", "turma"]

_ESCOPOS_COM_VALOR = frozenset({"curso", "semestre", "turma"})


@dataclass(frozen=True, slots=True)
class Audiencia:
    escopo: EscopoAudiencia
    valor: str | None = None

    def __post_init__(self) -> None:
        if self.escopo == "global" and self.valor is not None:
            raise ValueError(f"escopo='global' não admite valor (recebido: {self.valor!r})")
        if self.escopo in _ESCOPOS_COM_VALOR and not self.valor:
            raise ValueError(f"escopo={self.escopo!r} exige valor não-vazio")

    @classmethod
    def global_(cls) -> "Audiencia":
        return cls(escopo="global", valor=None)

    @classmethod
    def parse(cls, raw: str) -> "Audiencia":
        """Parse o formato canônico. Levanta ``ValueError`` se inválido."""
        if raw == "global":
            return cls.global_()
        if ":" not in raw:
            raise ValueError(f"audiência inválida: {raw!r} (faltou ':')")
        escopo_str, _, valor = raw.partition(":")
        if escopo_str not in _ESCOPOS_COM_VALOR:
            raise ValueError(f"escopo desconhecido: {escopo_str!r}")
        return cls(escopo=cast(EscopoAudiencia, escopo_str), valor=valor)

    def __str__(self) -> str:
        if self.escopo == "global":
            return "global"
        return f"{self.escopo}:{self.valor}"

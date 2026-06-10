"""``RespostaConversa`` — saída do orquestrador.

Carrega texto pronto + intenção + contexto recuperado para que o
entry point possa decidir UI adicional (ex.: inline keyboard com
botões "Adicionar ao Google Calendar" no caso CALENDARIO).
"""

from dataclasses import dataclass
from typing import Any

from chatbot.domain.conversa import Intencao


@dataclass(frozen=True, slots=True, kw_only=True)
class RespostaConversa:
    texto: str
    intencao: Intencao
    contexto: dict[str, Any]

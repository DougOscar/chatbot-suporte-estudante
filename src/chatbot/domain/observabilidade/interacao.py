"""Entidade ``Interacao`` — mensagem do aluno + resposta do bot.

Representa o que vai ser persistido no log. Não inclui ``id`` nem
``criado_em`` — esses são geridos pelo adapter (banco preenche).
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class Interacao:
    aluno_id: UUID | None
    telegram_user_id: int
    chat_id: int
    mensagem_recebida: str
    intencao_detectada: str
    resposta_enviada: str
    llm_provider: str
    llm_model: str
    prompt_versao: str
    contexto_recuperado: dict[str, Any] = field(default_factory=dict)
    tokens_entrada: int = 0
    tokens_saida: int = 0
    latencia_ms: int = 0
    erro: str | None = None

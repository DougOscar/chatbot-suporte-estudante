"""Ports do domínio de Observabilidade."""

from typing import Protocol, runtime_checkable

from chatbot.domain.observabilidade.interacao import Interacao


@runtime_checkable
class InteracaoLog(Protocol):
    """Sink de interações registradas pelo orquestrador de Conversa.

    Contrato: implementações **nunca devem levantar** exceções para o caller.
    Falhas de persistência viram log de aplicação (WARNING) — a resposta ao
    aluno não pode ser bloqueada por problema no log.
    """

    async def registrar(self, interacao: Interacao) -> None: ...

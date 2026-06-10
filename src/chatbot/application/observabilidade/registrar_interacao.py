"""Caso de uso ``RegistrarInteracao`` — fire-and-forget.

A persistência ocorre em background (:func:`asyncio.create_task`) — o
caller não bloqueia esperando o INSERT terminar. O port :class:`InteracaoLog`
já garante que nunca levanta; aqui adicionamos o agendamento.
"""

import asyncio

from chatbot.domain.observabilidade import Interacao, InteracaoLog


class RegistrarInteracao:
    def __init__(self, log: InteracaoLog) -> None:
        self._log = log
        # Referência forte para o GC não coletar tasks ainda em execução.
        self._background_tasks: set[asyncio.Task[None]] = set()

    def __call__(self, interacao: Interacao) -> None:
        """Agenda persistência em background. Requer event loop rodando."""
        task = asyncio.create_task(self._log.registrar(interacao))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def aguardar_pendentes(self) -> None:
        """Aguarda todas as tasks pendentes — usado em shutdown gracioso."""
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

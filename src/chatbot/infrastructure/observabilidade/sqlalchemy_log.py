"""Adapter SQLAlchemy do port :class:`InteracaoLog`.

Persiste em ``interacao``. Cumpre o contrato do port: **não levanta** —
falhas viram WARNING no log de aplicação.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatbot.domain.observabilidade import Interacao
from chatbot.infrastructure.persistence import models

_log = structlog.get_logger(__name__)


class SqlAlchemyInteracaoLog:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def registrar(self, interacao: Interacao) -> None:
        try:
            async with self._session_factory() as session:
                session.add(
                    models.Interacao(
                        aluno_id=interacao.aluno_id,
                        telegram_user_id=interacao.telegram_user_id,
                        chat_id=interacao.chat_id,
                        mensagem_recebida=interacao.mensagem_recebida,
                        intencao_detectada=interacao.intencao_detectada,
                        contexto_recuperado=interacao.contexto_recuperado,
                        resposta_enviada=interacao.resposta_enviada,
                        llm_provider=interacao.llm_provider,
                        llm_model=interacao.llm_model,
                        prompt_versao=interacao.prompt_versao,
                        tokens_entrada=interacao.tokens_entrada,
                        tokens_saida=interacao.tokens_saida,
                        latencia_ms=interacao.latencia_ms,
                        erro=interacao.erro,
                    )
                )
                await session.commit()
        except Exception as exc:
            _log.warning(
                "falha_registrar_interacao",
                error=str(exc),
                telegram_user_id=interacao.telegram_user_id,
            )

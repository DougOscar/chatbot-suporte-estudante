"""Entry point do bot do Telegram em modo polling.

Composition root: carrega a configuração, instancia engine/adapters,
monta o caso de uso ``RegistrarInteracao`` e registra os handlers.

Rodar:

    uv run python -m chatbot.interfaces.telegram_bot

ou (se o entry point ``chatbot-bot`` estiver instalado):

    uv run chatbot-bot

MVP: este entry point ainda **não** chama LLM nem usa intent routing
real. Os handlers respondem ``/start`` e ecoam texto livre, registrando
cada interação na tabela ``interacao``. Vai evoluir nas próximas fases.
"""

import time
from collections.abc import Callable, Coroutine
from typing import Any

import structlog
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from chatbot.application.observabilidade import RegistrarInteracao
from chatbot.config import get_settings
from chatbot.domain.observabilidade import Interacao
from chatbot.infrastructure.observabilidade.logging import configurar_logging
from chatbot.infrastructure.observabilidade.sqlalchemy_log import SqlAlchemyInteracaoLog
from chatbot.infrastructure.persistence.engine import create_engine, create_session_factory

_log = structlog.get_logger(__name__)

# Versão da persona/prompt — incrementar quando mudar o tom/formato das respostas.
PROMPT_VERSAO = "mvp-echo-0"

# PTB exige Coroutine (não Awaitable) no retorno dos handlers.
Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]
# Application com type-params explícitos — PTB é genérica e mypy strict exige.
AnyApplication = Application[Any, Any, Any, Any, Any, Any]


def _construir_handler_start(registrar: RegistrarInteracao) -> Handler:
    async def on_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if (msg := update.message) is None or (user := update.effective_user) is None:
            return

        resposta = (
            f"Olá, {user.first_name}! Sou o bot de suporte ao estudante. "
            "Por enquanto eu apenas ecoo mensagens e registro nosso diálogo no banco — "
            "as integrações com matrícula, calendário e base de conhecimento vêm nas "
            "próximas iterações."
        )
        inicio = time.monotonic()
        await msg.reply_text(resposta)
        latencia_ms = int((time.monotonic() - inicio) * 1000)

        registrar(
            Interacao(
                aluno_id=None,
                telegram_user_id=user.id,
                chat_id=msg.chat_id,
                mensagem_recebida=msg.text or "/start",
                intencao_detectada="SAUDACAO",
                resposta_enviada=resposta,
                llm_provider="none",
                llm_model="none",
                prompt_versao=PROMPT_VERSAO,
                latencia_ms=latencia_ms,
            )
        )

    return on_start


def _construir_handler_texto(registrar: RegistrarInteracao) -> Handler:
    async def on_text(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if (msg := update.message) is None or (user := update.effective_user) is None:
            return
        if msg.text is None:
            return

        texto = msg.text
        resposta = f"Você disse: {texto}"

        inicio = time.monotonic()
        await msg.reply_text(resposta)
        latencia_ms = int((time.monotonic() - inicio) * 1000)

        registrar(
            Interacao(
                aluno_id=None,
                telegram_user_id=user.id,
                chat_id=msg.chat_id,
                mensagem_recebida=texto,
                intencao_detectada="INDEFINIDO",
                resposta_enviada=resposta,
                llm_provider="none",
                llm_model="none",
                prompt_versao=PROMPT_VERSAO,
                latencia_ms=latencia_ms,
            )
        )

    return on_text


def construir_application(token: str, registrar: RegistrarInteracao) -> AnyApplication:
    """Monta a ``Application`` do python-telegram-bot já com os handlers."""
    application: AnyApplication = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", _construir_handler_start(registrar)))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, _construir_handler_texto(registrar))
    )
    return application


def main() -> None:
    settings = get_settings()
    configurar_logging(settings.observability)

    if settings.telegram.mode != "polling":
        raise NotImplementedError(
            f"Modo '{settings.telegram.mode}' ainda não suportado — use polling."
        )

    engine = create_engine()
    session_factory = create_session_factory(engine)
    log_adapter = SqlAlchemyInteracaoLog(session_factory)
    registrar = RegistrarInteracao(log_adapter)

    application = construir_application(
        settings.telegram.bot_token.get_secret_value(),
        registrar,
    )

    _log.info("bot_inicializado", mode="polling", prompt_versao=PROMPT_VERSAO)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

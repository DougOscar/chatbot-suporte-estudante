"""Entry point do bot do Telegram em modo polling.

Composition root: carrega config, instancia engine/adapters, monta os
casos de uso e registra handlers.

Rodar::

    uv run chatbot-bot
    # ou:
    uv run python -m chatbot.interfaces.telegram_bot

Estado atual (Fase 3): intent routing via ``ClassificarIntencao``,
contexto coletado por ``ProcessarMensagem``, resposta gerada por
``LLMGateway`` (Gemini por default, ou ``NullLLMGateway`` se a chave
estiver vazia).
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

from chatbot.application.calendario import ConsultarCalendario
from chatbot.application.conversa import (
    ClassificarIntencao,
    GerarResposta,
    ProcessarMensagem,
)
from chatbot.application.observabilidade import RegistrarInteracao
from chatbot.config import Settings, get_settings
from chatbot.domain.conversa import PERSONA_PADRAO, LLMGateway
from chatbot.domain.observabilidade import Interacao
from chatbot.infrastructure.llm.null_gateway import NullLLMGateway
from chatbot.infrastructure.observabilidade.logging import configurar_logging
from chatbot.infrastructure.observabilidade.sqlalchemy_log import SqlAlchemyInteracaoLog
from chatbot.infrastructure.persistence.calendario_repository import (
    SqlAlchemyCalendarioRepository,
)
from chatbot.infrastructure.persistence.engine import create_engine, create_session_factory

_log = structlog.get_logger(__name__)

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]
AnyApplication = Application[Any, Any, Any, Any, Any, Any]


def _construir_gateway_llm(settings: Settings) -> LLMGateway:
    """Escolhe o adapter de LLM conforme a config. Sem chave → fallback null."""
    if settings.llm.api_key is None or not settings.llm.api_key.get_secret_value():
        _log.warning("llm_api_key_ausente_usando_null_gateway")
        return NullLLMGateway()

    provider = settings.llm.provider
    if provider == "gemini":
        # Import lazy: extra `gemini` pode não estar instalado.
        from chatbot.infrastructure.llm.gemini_gateway import GeminiLLMGateway

        return GeminiLLMGateway(
            api_key=settings.llm.api_key.get_secret_value(),
            model=settings.llm.model,
        )

    raise NotImplementedError(
        f"Provedor de LLM '{provider}' ainda não implementado. Suportados: gemini."
    )


def _construir_handler_start(registrar: RegistrarInteracao) -> Handler:
    """Welcome determinístico — não passa pelo LLM (UX previsível na primeira interação)."""

    async def on_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if (msg := update.message) is None or (user := update.effective_user) is None:
            return

        resposta = (
            f"Olá, {user.first_name}! Sou o bot de suporte ao estudante. "
            "Pode me perguntar sobre o calendário, próximas datas e prazos. "
            "Outras integrações (matrícula, pagamentos, base de conhecimento) "
            "vêm nas próximas iterações."
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
                prompt_versao=PERSONA_PADRAO.versao,
                latencia_ms=latencia_ms,
            )
        )

    return on_start


def _construir_handler_texto(processar: ProcessarMensagem) -> Handler:
    async def on_text(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if (msg := update.message) is None or (user := update.effective_user) is None:
            return
        if msg.text is None:
            return

        resposta = await processar(
            telegram_user_id=user.id,
            chat_id=msg.chat_id,
            texto=msg.text,
        )
        await msg.reply_text(resposta)

    return on_text


def construir_application(
    token: str,
    registrar: RegistrarInteracao,
    processar: ProcessarMensagem,
) -> AnyApplication:
    application: AnyApplication = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", _construir_handler_start(registrar)))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, _construir_handler_texto(processar))
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

    calendario_repo = SqlAlchemyCalendarioRepository(session_factory)
    consultar_calendario = ConsultarCalendario(calendario_repo)

    gateway = _construir_gateway_llm(settings)
    gerar_resposta = GerarResposta(gateway=gateway, persona=PERSONA_PADRAO)
    processar = ProcessarMensagem(
        classificar=ClassificarIntencao(),
        consultar_calendario=consultar_calendario,
        gerar_resposta=gerar_resposta,
        registrar_interacao=registrar,
        persona=PERSONA_PADRAO,
    )

    application = construir_application(
        settings.telegram.bot_token.get_secret_value(),
        registrar,
        processar,
    )

    _log.info(
        "bot_inicializado",
        mode="polling",
        prompt_versao=PERSONA_PADRAO.versao,
        llm_provider=settings.llm.provider,
        llm_model=settings.llm.model,
    )
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

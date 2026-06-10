"""Entry point do bot do Telegram em modo polling.

Composition root: carrega a configuração, instancia engine/adapters,
monta os casos de uso e registra os handlers.

Rodar:

    uv run python -m chatbot.interfaces.telegram_bot

ou (entry point CLI):

    uv run chatbot-bot

Estado atual (Fase 2): handlers de ``/start``, intent simples para
calendário (regex), e fallback de eco. Sem LLM real ainda.
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
from chatbot.application.observabilidade import RegistrarInteracao
from chatbot.config import get_settings
from chatbot.domain.calendario import EventoCalendario
from chatbot.domain.observabilidade import Interacao
from chatbot.infrastructure.observabilidade.logging import configurar_logging
from chatbot.infrastructure.observabilidade.sqlalchemy_log import SqlAlchemyInteracaoLog
from chatbot.infrastructure.persistence.calendario_repository import (
    SqlAlchemyCalendarioRepository,
)
from chatbot.infrastructure.persistence.engine import create_engine, create_session_factory

_log = structlog.get_logger(__name__)

PROMPT_VERSAO = "mvp-echo-0"

# Regex de intenção CALENDARIO. Pega variações comuns em pt-BR.
_REGEX_CALENDARIO = (
    r"(?i)calend[áa]rio|"
    r"pr[óo]xim[oa]s?\s+(eventos?|datas?|provas?|aulas?)|"
    r"pr[óo]xim[oa]\s+prova|"
    r"prazo|"
    r"recesso"
)

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]
AnyApplication = Application[Any, Any, Any, Any, Any, Any]


def _construir_handler_start(registrar: RegistrarInteracao) -> Handler:
    async def on_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if (msg := update.message) is None or (user := update.effective_user) is None:
            return

        resposta = (
            f"Olá, {user.first_name}! Sou o bot de suporte ao estudante. "
            "Tente me perguntar sobre o calendário ou as próximas datas — "
            "estou começando a entender essas coisas. Outras integrações "
            "(matrícula, pagamentos, base de conhecimento) vêm nas próximas iterações."
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


def _formatar_eventos(eventos: list[EventoCalendario]) -> str:
    if not eventos:
        return "Não encontrei eventos próximos no calendário."
    linhas = ["Próximos eventos:"]
    for ev in eventos:
        data = ev.inicio.strftime("%d/%m/%Y")
        linhas.append(f"• {data} — {ev.titulo}")
    return "\n".join(linhas)


def _construir_handler_calendario(
    registrar: RegistrarInteracao,
    consultar: ConsultarCalendario,
) -> Handler:
    async def on_calendario(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if (msg := update.message) is None or (user := update.effective_user) is None:
            return
        if msg.text is None:
            return

        inicio = time.monotonic()
        eventos: list[EventoCalendario] = []
        erro: str | None = None
        try:
            eventos = await consultar()
            resposta = _formatar_eventos(eventos)
        except Exception as exc:
            resposta = "Tive um problema ao consultar o calendário agora. Tente em alguns minutos."
            erro = str(exc)
            _log.warning("falha_consultar_calendario", error=str(exc))

        await msg.reply_text(resposta)
        latencia_ms = int((time.monotonic() - inicio) * 1000)

        registrar(
            Interacao(
                aluno_id=None,
                telegram_user_id=user.id,
                chat_id=msg.chat_id,
                mensagem_recebida=msg.text,
                intencao_detectada="CALENDARIO",
                resposta_enviada=resposta,
                llm_provider="none",
                llm_model="none",
                prompt_versao=PROMPT_VERSAO,
                latencia_ms=latencia_ms,
                erro=erro,
                contexto_recuperado={"eventos_ids": [str(e.id) for e in eventos]},
            )
        )

    return on_calendario


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


def construir_application(
    token: str,
    registrar: RegistrarInteracao,
    consultar_calendario: ConsultarCalendario,
) -> AnyApplication:
    """Monta a ``Application`` do python-telegram-bot com os handlers.

    Ordem de registro importa: PTB tenta o primeiro handler que casa.
    Handlers específicos (calendário) antes do fallback (eco).
    """
    application: AnyApplication = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", _construir_handler_start(registrar)))
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(_REGEX_CALENDARIO),
            _construir_handler_calendario(registrar, consultar_calendario),
        )
    )
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

    calendario_repo = SqlAlchemyCalendarioRepository(session_factory)
    consultar_calendario = ConsultarCalendario(calendario_repo)

    application = construir_application(
        settings.telegram.bot_token.get_secret_value(),
        registrar,
        consultar_calendario,
    )

    _log.info("bot_inicializado", mode="polling", prompt_versao=PROMPT_VERSAO)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

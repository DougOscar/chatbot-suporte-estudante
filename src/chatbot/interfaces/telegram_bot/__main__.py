"""Entry point do bot do Telegram em modo polling.

Composition root: carrega config, instancia engine/adapters, monta os
casos de uso e registra handlers.

Rodar::

    uv run chatbot-bot
    # ou:
    uv run python -m chatbot.interfaces.telegram_bot

Estado atual (Fase 4c): handler de texto via ``ProcessarMensagem`` com
intent routing por regex + RAG; inline keyboard "Adicionar ao Google
Calendar" no caso CALENDARIO; ``/conectar_google`` + ``/concluir_oauth
<code>`` para o fluxo OAuth (mock em dev, real preparado).
"""

import time
from collections.abc import Callable, Coroutine
from typing import Any
from uuid import UUID

import structlog
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from chatbot.application.calendario import (
    Adicionado,
    AdicionarAoGoogleCalendar,
    ConcluirOAuthGoogle,
    ConsultarCalendario,
    EventoInexistente,
    IniciarOAuthGoogle,
    JaAdicionado,
    PrecisaAutorizar,
)
from chatbot.application.conhecimento import BuscarConhecimento
from chatbot.application.conversa import (
    ClassificarIntencao,
    GerarResposta,
    ProcessarMensagem,
)
from chatbot.application.financeiro import ConsultarProximoPagamento
from chatbot.application.matricula import ConsultarMatricula
from chatbot.application.observabilidade import RegistrarInteracao
from chatbot.config import Settings, get_settings
from chatbot.domain.calendario import CalendarioExterno, OAuthGoogleClient, OAuthGoogleStore
from chatbot.domain.conhecimento import EmbeddingGateway
from chatbot.domain.conversa import PERSONA_PADRAO, Intencao, LLMGateway
from chatbot.domain.financeiro import FinanceiroRepository
from chatbot.domain.matricula import MatriculaRepository
from chatbot.domain.observabilidade import Interacao
from chatbot.infrastructure.google.calendar.fernet_oauth_store import FernetOAuthStore
from chatbot.infrastructure.google.calendar.mock_calendar_adapter import (
    MockCalendarAdapter,
)
from chatbot.infrastructure.google.calendar.mock_oauth_client import MockOAuthClient
from chatbot.infrastructure.llm.null_embeddings import NullEmbeddingsGateway
from chatbot.infrastructure.llm.null_gateway import NullLLMGateway
from chatbot.infrastructure.observabilidade.logging import configurar_logging
from chatbot.infrastructure.observabilidade.sqlalchemy_log import SqlAlchemyInteracaoLog
from chatbot.infrastructure.persistence.calendario_repository import (
    SqlAlchemyCalendarioRepository,
)
from chatbot.infrastructure.persistence.engine import create_engine, create_session_factory
from chatbot.infrastructure.persistence.kb_repository import SqlAlchemyKbRepository
from chatbot.infrastructure.sistema_academico.mock_financeiro_repository import (
    MockFinanceiroRepository,
)
from chatbot.infrastructure.sistema_academico.mock_matricula_repository import (
    MockMatriculaRepository,
)

_log = structlog.get_logger(__name__)

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]
AnyApplication = Application[Any, Any, Any, Any, Any, Any]

_CALLBACK_PREFIX_ADD_GCAL = "add_gcal:"


# =====================================================================
# Composition helpers (escolhem mock vs real conforme config)
# =====================================================================


def _construir_gateway_llm(settings: Settings) -> LLMGateway:
    if settings.llm.api_key is None or not settings.llm.api_key.get_secret_value():
        _log.warning("llm_api_key_ausente_usando_null_gateway")
        return NullLLMGateway()
    if settings.llm.provider == "gemini":
        from chatbot.infrastructure.llm.gemini_gateway import GeminiLLMGateway

        return GeminiLLMGateway(
            api_key=settings.llm.api_key.get_secret_value(),
            model=settings.llm.model,
        )
    raise NotImplementedError(
        f"Provedor de LLM '{settings.llm.provider}' não implementado. Suportados: gemini."
    )


def _construir_matricula_repo(settings: Settings) -> MatriculaRepository:
    if settings.sistema_academico.mock:
        _log.info("sistema_academico_modo_mock", repo="matricula")
        return MockMatriculaRepository()
    raise NotImplementedError(
        "Adapter HTTP do sistema acadêmico ainda não definido — use "
        "SISTEMA_ACADEMICO_MOCK=true até a API real estar disponível."
    )


def _construir_financeiro_repo(settings: Settings) -> FinanceiroRepository:
    if settings.sistema_academico.mock:
        _log.info("sistema_academico_modo_mock", repo="financeiro")
        return MockFinanceiroRepository()
    raise NotImplementedError(
        "Adapter HTTP do sistema acadêmico ainda não definido — use "
        "SISTEMA_ACADEMICO_MOCK=true até a API real estar disponível."
    )


def _construir_embeddings_gateway(settings: Settings) -> EmbeddingGateway:
    embed = settings.embedding
    if embed.api_key is None or not embed.api_key.get_secret_value():
        _log.warning("embedding_api_key_ausente_usando_null_gateway")
        return NullEmbeddingsGateway()
    if embed.provider == "gemini":
        from chatbot.infrastructure.llm.gemini_embeddings import GeminiEmbeddingsGateway

        return GeminiEmbeddingsGateway(
            api_key=embed.api_key.get_secret_value(),
            model=embed.model,
        )
    raise NotImplementedError(
        f"Provedor de embeddings '{embed.provider}' não implementado. Suportados: gemini."
    )


def _construir_oauth_client(settings: Settings) -> OAuthGoogleClient:
    if settings.google_calendar.mock:
        _log.info("google_calendar_modo_mock", componente="oauth_client")
        return MockOAuthClient()
    raise NotImplementedError(
        "OAuth real do Google Calendar requer servidor HTTP para callback. "
        "Use GOOGLE_CALENDAR_MOCK=true em dev."
    )


def _construir_calendar_externo(settings: Settings) -> CalendarioExterno:
    if settings.google_calendar.mock:
        _log.info("google_calendar_modo_mock", componente="calendar_adapter")
        return MockCalendarAdapter()
    # Real: import lazy.
    from chatbot.infrastructure.google.calendar.google_calendar_adapter import (
        GoogleCalendarAdapter,
    )

    return GoogleCalendarAdapter()


def _construir_oauth_store(settings: Settings, session_factory: Any) -> OAuthGoogleStore:
    key_secret = settings.google_calendar.tokens_encryption_key
    if key_secret is None or not key_secret.get_secret_value():
        raise RuntimeError(
            "GOOGLE_CALENDAR_TOKENS_ENCRYPTION_KEY ausente. Gere com: "
            'python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        )
    return FernetOAuthStore(
        session_factory=session_factory,
        encryption_key=key_secret.get_secret_value().encode("utf-8"),
    )


# =====================================================================
# Handlers
# =====================================================================


def _registrar_interacao_simples(
    registrar: RegistrarInteracao,
    *,
    user_id: int,
    chat_id: int,
    mensagem: str,
    intencao: str,
    resposta: str,
    latencia_ms: int,
    erro: str | None = None,
) -> None:
    registrar(
        Interacao(
            aluno_id=None,
            telegram_user_id=user_id,
            chat_id=chat_id,
            mensagem_recebida=mensagem,
            intencao_detectada=intencao,
            resposta_enviada=resposta,
            llm_provider="none",
            llm_model="none",
            prompt_versao=PERSONA_PADRAO.versao,
            latencia_ms=latencia_ms,
            erro=erro,
        )
    )


def _construir_handler_start(registrar: RegistrarInteracao) -> Handler:
    async def on_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if (msg := update.message) is None or (user := update.effective_user) is None:
            return

        resposta = (
            f"Olá, {user.first_name}! Sou o bot de suporte ao estudante. "
            "Pode me perguntar sobre o calendário, próximas datas, sua matrícula, "
            "pagamentos, ou políticas internas. Para adicionar eventos ao seu "
            "Google Calendar, use /conectar_google primeiro."
        )
        inicio = time.monotonic()
        await msg.reply_text(resposta)
        _registrar_interacao_simples(
            registrar,
            user_id=user.id,
            chat_id=msg.chat_id,
            mensagem=msg.text or "/start",
            intencao="SAUDACAO",
            resposta=resposta,
            latencia_ms=int((time.monotonic() - inicio) * 1000),
        )

    return on_start


def _inline_keyboard_eventos(contexto: dict[str, Any]) -> InlineKeyboardMarkup | None:
    """Botão por evento no resultado de CALENDARIO."""
    eventos = contexto.get("eventos")
    if not isinstance(eventos, list) or not eventos:
        return None
    botoes = [
        [
            InlineKeyboardButton(
                f"Adicionar ao Google: {ev['titulo'][:40]}",
                callback_data=f"{_CALLBACK_PREFIX_ADD_GCAL}{ev['id']}",
            )
        ]
        for ev in eventos
        if isinstance(ev, dict) and "id" in ev and "titulo" in ev
    ]
    return InlineKeyboardMarkup(botoes) if botoes else None


def _construir_handler_texto(processar: ProcessarMensagem) -> Handler:
    async def on_text(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if (msg := update.message) is None or (user := update.effective_user) is None:
            return
        if msg.text is None:
            return

        resposta = await processar(telegram_user_id=user.id, chat_id=msg.chat_id, texto=msg.text)

        reply_markup = (
            _inline_keyboard_eventos(resposta.contexto)
            if resposta.intencao == Intencao.CALENDARIO
            else None
        )
        await msg.reply_text(resposta.texto, reply_markup=reply_markup)

    return on_text


def _construir_handler_conectar_google(
    registrar: RegistrarInteracao, iniciar: IniciarOAuthGoogle
) -> Handler:
    async def on_conectar(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if (msg := update.message) is None or (user := update.effective_user) is None:
            return
        inicio = time.monotonic()
        url = iniciar(telegram_user_id=user.id)
        resposta = (
            f"Abra esta URL para autorizar o bot a criar eventos no seu Google "
            f"Calendar:\n{url}\n\n"
            "Depois de autorizar, copie o code recebido e envie:\n"
            "/concluir_oauth <code>"
        )
        await msg.reply_text(resposta)
        _registrar_interacao_simples(
            registrar,
            user_id=user.id,
            chat_id=msg.chat_id,
            mensagem=msg.text or "/conectar_google",
            intencao="ADD_GCAL",
            resposta="<url de consent>",
            latencia_ms=int((time.monotonic() - inicio) * 1000),
        )

    return on_conectar


def _construir_handler_concluir_oauth(
    registrar: RegistrarInteracao, concluir: ConcluirOAuthGoogle
) -> Handler:
    async def on_concluir(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if (msg := update.message) is None or (user := update.effective_user) is None:
            return
        args = ctx.args if hasattr(ctx, "args") else None
        if not args:
            await msg.reply_text("Uso: /concluir_oauth <code>. Pegue o code da URL de consent.")
            return
        code = args[0]

        inicio = time.monotonic()
        erro: str | None = None
        try:
            await concluir(telegram_user_id=user.id, code=code)
            resposta = (
                "Conta Google conectada com sucesso! Agora você pode adicionar "
                "eventos ao seu calendário pelos botões na resposta de /calendário."
            )
        except Exception as exc:
            erro = str(exc)
            resposta = "Não consegui concluir a autorização. Tente /conectar_google de novo."
            _log.warning("falha_concluir_oauth", error=erro, user_id=user.id)

        await msg.reply_text(resposta)
        _registrar_interacao_simples(
            registrar,
            user_id=user.id,
            chat_id=msg.chat_id,
            mensagem="/concluir_oauth <code>",
            intencao="ADD_GCAL",
            resposta=resposta,
            latencia_ms=int((time.monotonic() - inicio) * 1000),
            erro=erro,
        )

    return on_concluir


def _construir_handler_callback_add_gcal(
    registrar: RegistrarInteracao,
    adicionar: AdicionarAoGoogleCalendar,
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]:
    async def on_callback(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user = update.effective_user
        if query is None or user is None or query.data is None:
            return
        await query.answer()  # tira o "loading" no cliente

        if not query.data.startswith(_CALLBACK_PREFIX_ADD_GCAL):
            return
        try:
            evento_id = UUID(query.data[len(_CALLBACK_PREFIX_ADD_GCAL) :])
        except ValueError:
            return

        inicio = time.monotonic()
        erro: str | None = None
        try:
            resultado = await adicionar(telegram_user_id=user.id, evento_id=evento_id)
        except Exception as exc:
            erro = str(exc)
            resultado = None
            _log.warning("falha_adicionar_gcal", error=erro, user_id=user.id)

        match resultado:
            case Adicionado(id_evento_google=eid):
                resposta = f"Evento adicionado ao seu Google Calendar (id {eid[:12]}…)."
            case JaAdicionado():
                resposta = "Esse evento já está no seu Google Calendar."
            case PrecisaAutorizar():
                resposta = (
                    "Preciso de autorização para acessar seu Google Calendar. Use /conectar_google."
                )
            case EventoInexistente():
                resposta = "Evento não encontrado. Tente listar os próximos novamente."
            case _:
                resposta = "Não consegui adicionar agora. Tente em alguns minutos."

        # query.message é MaybeInaccessibleMessage — checa antes de acessar.
        chat_id_for_reply = (
            query.message.chat.id
            if query.message is not None and hasattr(query.message, "chat")
            else user.id
        )
        await update.get_bot().send_message(chat_id=chat_id_for_reply, text=resposta)

        _registrar_interacao_simples(
            registrar,
            user_id=user.id,
            chat_id=chat_id_for_reply,
            mensagem=f"callback {query.data}",
            intencao="ADD_GCAL",
            resposta=resposta,
            latencia_ms=int((time.monotonic() - inicio) * 1000),
            erro=erro,
        )

    return on_callback


# =====================================================================
# Application factory + main
# =====================================================================


def construir_application(
    token: str,
    *,
    registrar: RegistrarInteracao,
    processar: ProcessarMensagem,
    iniciar_oauth: IniciarOAuthGoogle,
    concluir_oauth: ConcluirOAuthGoogle,
    adicionar_gcal: AdicionarAoGoogleCalendar,
) -> AnyApplication:
    application: AnyApplication = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", _construir_handler_start(registrar)))
    application.add_handler(
        CommandHandler(
            "conectar_google",
            _construir_handler_conectar_google(registrar, iniciar_oauth),
        )
    )
    application.add_handler(
        CommandHandler(
            "concluir_oauth",
            _construir_handler_concluir_oauth(registrar, concluir_oauth),
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            _construir_handler_callback_add_gcal(registrar, adicionar_gcal),
            pattern=f"^{_CALLBACK_PREFIX_ADD_GCAL}",
        )
    )
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

    matricula_repo = _construir_matricula_repo(settings)
    consultar_matricula = ConsultarMatricula(matricula_repo)

    financeiro_repo = _construir_financeiro_repo(settings)
    consultar_proximo_pagamento = ConsultarProximoPagamento(financeiro_repo)

    kb_repo = SqlAlchemyKbRepository(session_factory)
    embeddings_gateway = _construir_embeddings_gateway(settings)
    buscar_conhecimento = BuscarConhecimento(repository=kb_repo, embeddings=embeddings_gateway)

    # Google Calendar OAuth + adapter externo
    oauth_client = _construir_oauth_client(settings)
    oauth_store = _construir_oauth_store(settings, session_factory)
    calendario_externo = _construir_calendar_externo(settings)
    iniciar_oauth = IniciarOAuthGoogle(oauth_client)
    concluir_oauth = ConcluirOAuthGoogle(client=oauth_client, store=oauth_store)
    adicionar_gcal = AdicionarAoGoogleCalendar(
        repository=calendario_repo,
        externo=calendario_externo,
        store=oauth_store,
    )

    gateway = _construir_gateway_llm(settings)
    gerar_resposta = GerarResposta(gateway=gateway, persona=PERSONA_PADRAO)
    processar = ProcessarMensagem(
        classificar=ClassificarIntencao(),
        consultar_calendario=consultar_calendario,
        consultar_matricula=consultar_matricula,
        consultar_proximo_pagamento=consultar_proximo_pagamento,
        buscar_conhecimento=buscar_conhecimento,
        gerar_resposta=gerar_resposta,
        registrar_interacao=registrar,
        persona=PERSONA_PADRAO,
    )

    application = construir_application(
        settings.telegram.bot_token.get_secret_value(),
        registrar=registrar,
        processar=processar,
        iniciar_oauth=iniciar_oauth,
        concluir_oauth=concluir_oauth,
        adicionar_gcal=adicionar_gcal,
    )

    _log.info(
        "bot_inicializado",
        mode="polling",
        prompt_versao=PERSONA_PADRAO.versao,
        llm_provider=settings.llm.provider,
        google_calendar_mock=settings.google_calendar.mock,
    )
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

"""Caso de uso ``ProcessarMensagem`` — orquestrador da Conversa.

Recebe mensagem do Telegram, classifica intenção, coleta contexto do
bounded context adequado, chama o LLM para formatar resposta, e dispara
o registro de interação (fire-and-forget).

Esta é a "linha do tempo" de uma mensagem — todas as integrações de
contexto passam por aqui. Branches por intenção viram explícitos como
``elif intencao == Intencao.X``. Quando o número de intenções crescer,
isso pode virar um dispatch table.
"""

import time
from typing import Any

import structlog

from chatbot.application.calendario import ConsultarCalendario
from chatbot.application.conversa.classificar_intencao import ClassificarIntencao
from chatbot.application.conversa.gerar_resposta import GerarResposta
from chatbot.application.financeiro import ConsultarProximoPagamento
from chatbot.application.matricula import ConsultarMatricula
from chatbot.application.observabilidade import RegistrarInteracao
from chatbot.domain.conversa import Intencao, Persona, RespostaLLM
from chatbot.domain.observabilidade import Interacao

_log = structlog.get_logger(__name__)

_MSG_ERRO_FALLBACK = (
    "Tive um problema agora para processar sua mensagem. Tente novamente em alguns minutos."
)


class ProcessarMensagem:
    def __init__(
        self,
        *,
        classificar: ClassificarIntencao,
        consultar_calendario: ConsultarCalendario,
        consultar_matricula: ConsultarMatricula,
        consultar_proximo_pagamento: ConsultarProximoPagamento,
        gerar_resposta: GerarResposta,
        registrar_interacao: RegistrarInteracao,
        persona: Persona,
    ) -> None:
        self._classificar = classificar
        self._consultar_calendario = consultar_calendario
        self._consultar_matricula = consultar_matricula
        self._consultar_proximo_pagamento = consultar_proximo_pagamento
        self._gerar_resposta = gerar_resposta
        self._registrar = registrar_interacao
        self._persona = persona

    async def __call__(
        self,
        *,
        telegram_user_id: int,
        chat_id: int,
        texto: str,
    ) -> str:
        inicio = time.monotonic()
        intencao = self._classificar(texto)

        contexto: dict[str, Any] = {}
        resposta_llm: RespostaLLM | None = None
        resposta_texto = _MSG_ERRO_FALLBACK
        erro: str | None = None

        try:
            contexto = await self._coletar_contexto(intencao, telegram_user_id)
            resposta_llm = await self._gerar_resposta(
                intencao=intencao,
                contexto=contexto,
                mensagem_usuario=texto,
            )
            resposta_texto = resposta_llm.texto or _MSG_ERRO_FALLBACK
        except Exception as exc:
            erro = str(exc)
            _log.warning(
                "falha_processar_mensagem",
                error=erro,
                intencao=str(intencao),
            )

        latencia_ms = int((time.monotonic() - inicio) * 1000)

        self._registrar(
            Interacao(
                aluno_id=None,
                telegram_user_id=telegram_user_id,
                chat_id=chat_id,
                mensagem_recebida=texto,
                intencao_detectada=intencao.value,
                resposta_enviada=resposta_texto,
                llm_provider=resposta_llm.provider if resposta_llm else "none",
                llm_model=resposta_llm.modelo if resposta_llm else "none",
                prompt_versao=self._persona.versao,
                tokens_entrada=resposta_llm.tokens_entrada if resposta_llm else 0,
                tokens_saida=resposta_llm.tokens_saida if resposta_llm else 0,
                latencia_ms=latencia_ms,
                erro=erro,
                contexto_recuperado=contexto,
            )
        )

        return resposta_texto

    async def _coletar_contexto(self, intencao: Intencao, telegram_user_id: int) -> dict[str, Any]:
        """Contexto estruturado em DTOs serializáveis (JSON-safe)."""
        if intencao == Intencao.CALENDARIO:
            eventos = await self._consultar_calendario()
            return {
                "eventos": [
                    {
                        "id": str(e.id),
                        "titulo": e.titulo,
                        "descricao": e.descricao,
                        "inicio": e.inicio.isoformat(),
                        "local": e.local,
                        "audiencia": str(e.audiencia),
                    }
                    for e in eventos
                ]
            }

        if intencao == Intencao.MATRICULA:
            matricula = await self._consultar_matricula(telegram_user_id=telegram_user_id)
            if matricula is None:
                return {"matricula": None}
            return {
                "matricula": {
                    "matricula_id_externo": matricula.matricula_id_externo,
                    "status": matricula.status.value,
                    "curso": matricula.curso,
                    "semestre_atual": matricula.semestre_atual,
                    "nome_aluno": matricula.nome_aluno,
                    "desde": (matricula.desde.isoformat() if matricula.desde else None),
                }
            }

        if intencao == Intencao.PROXIMO_PAGAMENTO:
            pagamento = await self._consultar_proximo_pagamento(telegram_user_id=telegram_user_id)
            if pagamento is None:
                return {"pagamento": None}
            return {
                "pagamento": {
                    "referencia": pagamento.referencia,
                    "valor": str(pagamento.valor),
                    "vencimento": pagamento.vencimento.isoformat(),
                    "status": pagamento.status.value,
                    "url_boleto": pagamento.url_boleto,
                }
            }

        return {}

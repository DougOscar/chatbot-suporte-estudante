"""``CalendarioExterno`` fake — não chama Google, só gera id fictício.

O id retornado é determinístico em função do ``evento.id`` para que
testes possam validar dedup sem coordenação extra.
"""

from chatbot.domain.calendario import EventoCalendario, OAuthToken


class MockCalendarAdapter:
    async def criar_evento(self, *, token: OAuthToken, evento: EventoCalendario) -> str:
        # Não valida o token; em dev qualquer token serve.
        return f"mock-gevent-{evento.id}"

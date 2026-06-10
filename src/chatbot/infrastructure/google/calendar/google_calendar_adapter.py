"""``CalendarioExterno`` real — Google Calendar API v3 via ``google-api-python-client``.

Lazy import. Não cobre o fluxo OAuth (callback HTTP), apenas a chamada de
``events.insert`` dado um token já adquirido por outra camada.

Use em conjunto com ``OAuthGoogleClient`` real (não implementado ainda)
ou armazenando tokens manualmente. Em dev, prefira o ``MockCalendarAdapter``.
"""

import asyncio

from chatbot.domain.calendario import EventoCalendario, OAuthToken

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError as _exc:  # pragma: no cover
    raise ImportError(
        "Pacotes Google ausentes. Já são deps runtime (google-api-python-client, "
        "google-auth) — rode `uv sync`."
    ) from _exc


class GoogleCalendarAdapter:
    _TIMEZONE = "America/Sao_Paulo"

    async def criar_evento(self, *, token: OAuthToken, evento: EventoCalendario) -> str:
        creds = Credentials(  # type: ignore[no-untyped-call]
            token=token.access_token, refresh_token=token.refresh_token
        )

        body: dict[str, object] = {
            "summary": evento.titulo,
            "description": evento.descricao or "",
            "start": {
                "dateTime": evento.inicio.isoformat(),
                "timeZone": self._TIMEZONE,
            },
            "end": {
                "dateTime": (evento.fim or evento.inicio).isoformat(),
                "timeZone": self._TIMEZONE,
            },
            "extendedProperties": {"private": {"bot_evento_id": str(evento.id)}},
        }
        if evento.local:
            body["location"] = evento.local

        # google-api-python-client é síncrono. Joga para executor para não
        # bloquear o event loop do bot.
        def _criar() -> str:
            service = build("calendar", "v3", credentials=creds, cache_discovery=False)
            criado = service.events().insert(calendarId="primary", body=body).execute()
            return str(criado["id"])

        return await asyncio.get_event_loop().run_in_executor(None, _criar)

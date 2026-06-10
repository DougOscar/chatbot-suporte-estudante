"""``OAuthGoogleClient`` fake — emula consent URL e troca de code por token.

Útil em dev sem domínio público (não há callback). O fluxo no Telegram
fica: bot envia URL fake → aluno "autoriza" mandando ``/concluir_oauth
<qualquer-code>`` → mock retorna token fixo.
"""

from datetime import UTC, datetime, timedelta

from chatbot.domain.calendario import OAuthToken


class MockOAuthClient:
    _CONSENT_BASE = "https://example.com/oauth-fake/consent"

    def url_consent(self, *, state: str) -> str:
        return f"{self._CONSENT_BASE}?state={state}"

    async def trocar_code(self, code: str) -> OAuthToken:
        # Aceita qualquer code não-vazio.
        if not code.strip():
            raise ValueError("code vazio")
        return OAuthToken(
            access_token=f"mock-access-{code[:8]}",
            refresh_token=f"mock-refresh-{code[:8]}",
            expira_em=datetime.now(UTC) + timedelta(hours=1),
        )

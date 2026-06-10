"""``IniciarOAuthGoogle`` — gera URL de consent que o aluno deve abrir."""

from chatbot.domain.calendario import OAuthGoogleClient


class IniciarOAuthGoogle:
    def __init__(self, client: OAuthGoogleClient) -> None:
        self._client = client

    def __call__(self, *, telegram_user_id: int) -> str:
        # `state` evita CSRF e nos diz qual aluno está autorizando no callback.
        # Em mock, é só um identificador opaco.
        return self._client.url_consent(state=str(telegram_user_id))

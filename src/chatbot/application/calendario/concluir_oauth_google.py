"""``ConcluirOAuthGoogle`` — troca code por token e persiste cifrado."""

from chatbot.domain.calendario import OAuthGoogleClient, OAuthGoogleStore


class ConcluirOAuthGoogle:
    def __init__(self, *, client: OAuthGoogleClient, store: OAuthGoogleStore) -> None:
        self._client = client
        self._store = store

    async def __call__(self, *, telegram_user_id: int, code: str) -> None:
        token = await self._client.trocar_code(code)
        await self._store.salvar(telegram_user_id=telegram_user_id, token=token)

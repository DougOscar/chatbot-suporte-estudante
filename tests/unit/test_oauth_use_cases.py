"""Testes de ``IniciarOAuthGoogle`` + ``ConcluirOAuthGoogle`` com fakes."""

from uuid import UUID

from chatbot.application.calendario import ConcluirOAuthGoogle, IniciarOAuthGoogle
from chatbot.domain.calendario import OAuthToken


class _FakeClient:
    def __init__(self) -> None:
        self.consent_calls: list[str] = []
        self.code_calls: list[str] = []

    def url_consent(self, *, state: str) -> str:
        self.consent_calls.append(state)
        return f"https://exemplo/consent?state={state}"

    async def trocar_code(self, code: str) -> OAuthToken:
        self.code_calls.append(code)
        return OAuthToken(access_token=f"a-{code}", refresh_token=f"r-{code}")


class _FakeStore:
    def __init__(self) -> None:
        self.salvos: list[tuple[int, OAuthToken]] = []

    async def salvar(self, *, telegram_user_id: int, token: OAuthToken) -> None:
        self.salvos.append((telegram_user_id, token))

    async def buscar(self, telegram_user_id: int) -> OAuthToken | None:
        return None

    async def registrar_adicao(
        self, *, telegram_user_id: int, evento_id: UUID, id_evento_google: str
    ) -> None: ...

    async def adicao_existente(self, *, telegram_user_id: int, evento_id: UUID) -> str | None:
        return None


def test_iniciar_passa_telegram_user_id_como_state() -> None:
    client = _FakeClient()
    uc = IniciarOAuthGoogle(client)

    url = uc(telegram_user_id=12345)

    assert "state=12345" in url
    assert client.consent_calls == ["12345"]


async def test_concluir_troca_code_e_salva() -> None:
    client = _FakeClient()
    store = _FakeStore()
    uc = ConcluirOAuthGoogle(client=client, store=store)

    await uc(telegram_user_id=99, code="cod-xyz")

    assert client.code_calls == ["cod-xyz"]
    assert len(store.salvos) == 1
    salvo_user, salvo_token = store.salvos[0]
    assert salvo_user == 99
    assert salvo_token.access_token == "a-cod-xyz"

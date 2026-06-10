"""Storage de tokens OAuth Google com criptografia Fernet em repouso.

Token claro (``OAuthToken``) só existe em memória. No banco, ``access_token``
e ``refresh_token`` ficam como ``bytea`` cifrado (campos
``access_token_cifrado``/``refresh_token_cifrado`` em ``oauth_google_token``).

O ``aluno_id`` (FK) vem do UPSERT na tabela ``aluno`` por ``telegram_user_id``
— onboarding implícito enquanto o fluxo formal não existe.
"""

from uuid import UUID

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatbot.domain.calendario import OAuthToken
from chatbot.infrastructure.persistence import models


class FernetOAuthStore:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        encryption_key: bytes,
    ) -> None:
        self._session_factory = session_factory
        self._fernet = Fernet(encryption_key)

    # --- API pública (port OAuthGoogleStore) ---

    async def salvar(self, *, telegram_user_id: int, token: OAuthToken) -> None:
        async with self._session_factory() as session:
            aluno_id = await self._garantir_aluno(session, telegram_user_id)
            access_cifrado = self._fernet.encrypt(token.access_token.encode("utf-8"))
            refresh_cifrado = (
                self._fernet.encrypt(token.refresh_token.encode("utf-8"))
                if token.refresh_token
                else None
            )

            stmt = pg_insert(models.OAuthGoogleToken).values(
                aluno_id=aluno_id,
                provider="google",
                access_token_cifrado=access_cifrado,
                refresh_token_cifrado=refresh_cifrado,
                expira_em=token.expira_em,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["aluno_id", "provider"],
                set_={
                    "access_token_cifrado": stmt.excluded.access_token_cifrado,
                    "refresh_token_cifrado": stmt.excluded.refresh_token_cifrado,
                    "expira_em": stmt.excluded.expira_em,
                },
            )
            await session.execute(stmt)
            await session.commit()

    async def buscar(self, telegram_user_id: int) -> OAuthToken | None:
        async with self._session_factory() as session:
            stmt = (
                select(models.OAuthGoogleToken)
                .join(models.Aluno, models.OAuthGoogleToken.aluno_id == models.Aluno.id)
                .where(models.Aluno.telegram_user_id == telegram_user_id)
                .where(models.OAuthGoogleToken.provider == "google")
            )
            row = (await session.execute(stmt)).scalar_one_or_none()

        if row is None:
            return None

        access = self._fernet.decrypt(row.access_token_cifrado).decode("utf-8")
        refresh = (
            self._fernet.decrypt(row.refresh_token_cifrado).decode("utf-8")
            if row.refresh_token_cifrado
            else None
        )
        return OAuthToken(access_token=access, refresh_token=refresh, expira_em=row.expira_em)

    async def registrar_adicao(
        self,
        *,
        telegram_user_id: int,
        evento_id: UUID,
        id_evento_google: str,
    ) -> None:
        async with self._session_factory() as session:
            aluno_id = await self._garantir_aluno(session, telegram_user_id)
            session.add(
                models.AdicaoCalendarioExterno(
                    aluno_id=aluno_id,
                    evento_id=evento_id,
                    id_evento_google=id_evento_google,
                )
            )
            await session.commit()

    async def adicao_existente(self, *, telegram_user_id: int, evento_id: UUID) -> str | None:
        async with self._session_factory() as session:
            stmt = (
                select(models.AdicaoCalendarioExterno.id_evento_google)
                .join(
                    models.Aluno,
                    models.AdicaoCalendarioExterno.aluno_id == models.Aluno.id,
                )
                .where(models.Aluno.telegram_user_id == telegram_user_id)
                .where(models.AdicaoCalendarioExterno.evento_id == evento_id)
            )
            return (await session.execute(stmt)).scalar_one_or_none()

    # --- Helper interno ---

    async def _garantir_aluno(self, session: AsyncSession, telegram_user_id: int) -> UUID:
        """UPSERT no ``aluno`` por ``telegram_user_id``. Retorna o ``aluno.id``.

        DO UPDATE no próprio campo (no-op) é necessário porque RETURNING não
        funciona com ON CONFLICT DO NOTHING quando há conflito.
        """
        base = pg_insert(models.Aluno).values(telegram_user_id=telegram_user_id)
        stmt = base.on_conflict_do_update(
            index_elements=["telegram_user_id"],
            set_={"telegram_user_id": base.excluded.telegram_user_id},
        ).returning(models.Aluno.id)
        result = await session.execute(stmt)
        aluno_id: UUID = result.scalar_one()
        return aluno_id

"""unique constraint em oauth_google_token (aluno_id, provider)

Revision ID: 0002_oauth_unique
Revises: 0001_inicial
Create Date: 2026-06-10

Necessário para o UPSERT do storage Fernet (Fase 4c). Um aluno só pode
ter 1 token ativo por provedor.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_oauth_unique"
down_revision: str | Sequence[str] | None = "0001_inicial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_oauth_token_aluno_provider",
        "oauth_google_token",
        ["aluno_id", "provider"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_oauth_token_aluno_provider",
        "oauth_google_token",
        type_="unique",
    )

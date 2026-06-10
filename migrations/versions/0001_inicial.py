"""inicial — extensão pgvector + schema base

Revision ID: 0001_inicial
Revises:
Create Date: 2026-06-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_inicial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Mantido em sincronia com chatbot.infrastructure.persistence.models.EMBEDDING_DIM.
EMBEDDING_DIM = 768


def upgrade() -> None:
    # 1. Extensão pgvector — pré-requisito para a coluna `kb_chunk.embedding`.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Tabelas raiz (sem FKs para outras tabelas do projeto).
    op.create_table(
        "aluno",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("nome", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("matricula_id_externo", sa.Text(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_aluno_telegram_user_id",
        "aluno",
        ["telegram_user_id"],
        unique=True,
    )

    op.create_table(
        "evento_calendario",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fim", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dia_inteiro", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("audiencia", sa.Text(), server_default=sa.text("'global'"), nullable=False),
        sa.Column("local", sa.Text(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_evento_calendario_inicio", "evento_calendario", ["inicio"])
    op.create_index("ix_evento_calendario_audiencia", "evento_calendario", ["audiencia"])

    op.create_table(
        "documento_kb",
        sa.Column("id", sa.Text(), primary_key=True),  # google_doc_id
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("atualizado_em_origem", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "sincronizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("hash_conteudo", sa.String(length=64), nullable=True),
    )

    # 3. Tabelas dependentes.
    op.create_table(
        "matricula_cache",
        sa.Column(
            "aluno_id",
            sa.Uuid(),
            sa.ForeignKey("aluno.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("curso", sa.Text(), nullable=True),
        sa.Column("semestre_atual", sa.SmallInteger(), nullable=True),
        sa.Column("desde", sa.Date(), nullable=True),
        sa.Column(
            "consultada_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "oauth_google_token",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "aluno_id",
            sa.Uuid(),
            sa.ForeignKey("aluno.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(length=32),
            server_default=sa.text("'google'"),
            nullable=False,
        ),
        sa.Column("access_token_cifrado", sa.LargeBinary(), nullable=False),
        sa.Column("refresh_token_cifrado", sa.LargeBinary(), nullable=True),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_oauth_google_token_aluno_id", "oauth_google_token", ["aluno_id"])

    op.create_table(
        "adicao_calendario_externo",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "aluno_id",
            sa.Uuid(),
            sa.ForeignKey("aluno.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "evento_id",
            sa.Uuid(),
            sa.ForeignKey("evento_calendario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("id_evento_google", sa.Text(), nullable=False),
        sa.Column(
            "adicionado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("aluno_id", "evento_id", name="uq_adicao_aluno_evento"),
    )

    op.create_table(
        "kb_chunk",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "documento_id",
            sa.Text(),
            sa.ForeignKey("documento_kb.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("indice", sa.Integer(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_kb_chunk_documento_id", "kb_chunk", ["documento_id"])
    # HNSW para busca por similaridade de cosseno. Requer pgvector >= 0.5.
    op.create_index(
        "ix_kb_chunk_embedding_hnsw",
        "kb_chunk",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_table(
        "interacao",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "aluno_id",
            sa.Uuid(),
            sa.ForeignKey("aluno.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("mensagem_recebida", sa.Text(), nullable=False),
        sa.Column("intencao_detectada", sa.Text(), nullable=False),
        sa.Column(
            "contexto_recuperado",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("resposta_enviada", sa.Text(), nullable=False),
        sa.Column("llm_provider", sa.String(length=32), nullable=False),
        sa.Column("llm_model", sa.String(length=64), nullable=False),
        sa.Column("prompt_versao", sa.String(length=32), nullable=False),
        sa.Column(
            "tokens_entrada",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "tokens_saida",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "latencia_ms",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_interacao_criado_em", "interacao", ["criado_em"])
    op.create_index(
        "ix_interacao_aluno_criado_em",
        "interacao",
        ["aluno_id", "criado_em"],
    )


def downgrade() -> None:
    # Drop em ordem inversa às dependências.
    op.drop_table("interacao")
    op.drop_index("ix_kb_chunk_embedding_hnsw", table_name="kb_chunk")
    op.drop_table("kb_chunk")
    op.drop_table("adicao_calendario_externo")
    op.drop_table("oauth_google_token")
    op.drop_table("matricula_cache")
    op.drop_table("documento_kb")
    op.drop_table("evento_calendario")
    op.drop_table("aluno")
    op.execute("DROP EXTENSION IF EXISTS vector")

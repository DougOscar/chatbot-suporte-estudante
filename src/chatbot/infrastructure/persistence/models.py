"""Modelos SQLAlchemy correspondentes ao schema em ``docs/05-Modelagem/Schema-Banco.md``.

Modelos vivem em ``infrastructure`` por design (Hexagonal): são detalhe
de implementação da persistência, não pertencem ao ``domain``. Entidades
puras de domínio virão depois, em ``domain/<contexto>/`` com mapeamento
explícito repository → modelo.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from chatbot.infrastructure.persistence.base import Base

# Dimensão dos vetores de embedding. Alinhada com o default do projeto
# (Gemini text-embedding-004 = 768). Trocar este valor exige nova migração.
EMBEDDING_DIM = 768


class Aluno(Base):
    __tablename__ = "aluno"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    nome: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    matricula_id_externo: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class MatriculaCache(Base):
    __tablename__ = "matricula_cache"

    aluno_id: Mapped[UUID] = mapped_column(
        ForeignKey("aluno.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(Text)
    curso: Mapped[str | None] = mapped_column(Text, nullable=True)
    semestre_atual: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    desde: Mapped[date | None] = mapped_column(Date, nullable=True)
    consultada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OAuthGoogleToken(Base):
    __tablename__ = "oauth_google_token"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    aluno_id: Mapped[UUID] = mapped_column(ForeignKey("aluno.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(32), default="google")
    access_token_cifrado: Mapped[bytes] = mapped_column(LargeBinary)
    refresh_token_cifrado: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("aluno_id", "provider", name="uq_oauth_token_aluno_provider"),
    )


class EventoCalendario(Base):
    __tablename__ = "evento_calendario"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    titulo: Mapped[str] = mapped_column(Text)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dia_inteiro: Mapped[bool] = mapped_column(Boolean, server_default="false")
    audiencia: Mapped[str] = mapped_column(Text, server_default="global", index=True)
    local: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class AdicaoCalendarioExterno(Base):
    __tablename__ = "adicao_calendario_externo"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    aluno_id: Mapped[UUID] = mapped_column(ForeignKey("aluno.id", ondelete="CASCADE"))
    evento_id: Mapped[UUID] = mapped_column(ForeignKey("evento_calendario.id", ondelete="CASCADE"))
    id_evento_google: Mapped[str] = mapped_column(Text)
    adicionado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (UniqueConstraint("aluno_id", "evento_id", name="uq_adicao_aluno_evento"),)


class DocumentoKB(Base):
    __tablename__ = "documento_kb"

    # PK é o google_doc_id direto — não inventamos UUID.
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    titulo: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    atualizado_em_origem: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sincronizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    hash_conteudo: Mapped[str | None] = mapped_column(String(64), nullable=True)


class KBChunk(Base):
    __tablename__ = "kb_chunk"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    documento_id: Mapped[str] = mapped_column(
        ForeignKey("documento_kb.id", ondelete="CASCADE"), index=True
    )
    indice: Mapped[int] = mapped_column(Integer)
    texto: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Interacao(Base):
    __tablename__ = "interacao"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    aluno_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("aluno.id", ondelete="SET NULL"), nullable=True
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    mensagem_recebida: Mapped[str] = mapped_column(Text)
    intencao_detectada: Mapped[str] = mapped_column(Text)
    contexto_recuperado: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    resposta_enviada: Mapped[str] = mapped_column(Text)
    llm_provider: Mapped[str] = mapped_column(String(32))
    llm_model: Mapped[str] = mapped_column(String(64))
    prompt_versao: Mapped[str] = mapped_column(String(32))
    tokens_entrada: Mapped[int] = mapped_column(Integer, server_default="0")
    tokens_saida: Mapped[int] = mapped_column(Integer, server_default="0")
    latencia_ms: Mapped[int] = mapped_column(Integer, server_default="0")
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Composite para consultas "últimas interações por aluno".
    __table_args__ = (Index("ix_interacao_aluno_criado_em", "aluno_id", "criado_em"),)

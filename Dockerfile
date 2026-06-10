# syntax=docker/dockerfile:1.7
# Multi-stage build: uv como builder, python:3.12-slim como runtime.
# A imagem final não tem uv nem build tools — apenas o .venv resolvido.

# =====================================================================
# Stage 1: builder com uv
# =====================================================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Camada 1 — só deps (cache estável até pyproject/lock mudar).
# `--mount=type=cache` aceleraria builds repetidos mas exige BuildKit/buildx
# — omitido para compatibilidade com Docker sem buildx. CI tem buildx por padrão.
COPY pyproject.toml uv.lock .python-version README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Camada 2 — código + install do projeto (para o entry point `chatbot-bot`).
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# =====================================================================
# Stage 2: runtime minimal
# =====================================================================
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Usuário não-root.
RUN groupadd --gid 1000 chatbot \
 && useradd --uid 1000 --gid chatbot --create-home --shell /bin/bash chatbot

# .venv + código pronto vindo do builder.
COPY --from=builder --chown=chatbot:chatbot /app/.venv /app/.venv
COPY --from=builder --chown=chatbot:chatbot /app/src /app/src

# Migrações + alembic.ini (necessários para `alembic upgrade head`).
COPY --chown=chatbot:chatbot alembic.ini ./
COPY --chown=chatbot:chatbot migrations/ ./migrations/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER chatbot

# Em webhook mode o PTB escuta nesta porta — alinhado com a convenção
# de PaaS (Fly.io / Cloud Run lêem $PORT).
EXPOSE 8080

CMD ["chatbot-bot"]

---
title: Variáveis de Ambiente
tags: [operacoes, configuracao]
---

# Variáveis de Ambiente

Referência completa do `.env`. Template em `.env.example` na raiz do projeto.

## Telegram

| Variável | Obrigatória | Descrição |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | sim | Token do BotFather. Ver [[03-Integracoes/Telegram-BotFather]] |
| `TELEGRAM_MODE` | sim | `polling` (dev) ou `webhook` (prod) |
| `TELEGRAM_WEBHOOK_URL` | só em webhook | URL pública HTTPS que recebe os updates |

## Banco de dados

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | sim | DSN do Postgres. Formato: `postgresql+psycopg://user:senha@host:porta/banco` |

Detalhes em [[04-Operacoes/Banco-de-Dados]].

## LLM

| Variável | Obrigatória | Descrição |
|---|---|---|
| `LLM_PROVIDER` | sim | `gemini`, `anthropic`, `openai`, `groq` ou `ollama` |
| `LLM_MODEL` | sim | Identificador do modelo (`gemini-2.5-flash`, `claude-haiku-4-5`, ...) |
| `LLM_API_KEY` | sim (exceto ollama local) | Chave de API do provedor |

Ver comparativo em [[03-Integracoes/LLM-Provedores]].

## Embeddings (RAG)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `EMBEDDING_PROVIDER` | sim | `gemini`, `openai` ou `sentence-transformers` |
| `EMBEDDING_MODEL` | sim | Identificador do modelo de embedding |
| `EMBEDDING_API_KEY` | quando aplicável | Pode ser igual à `LLM_API_KEY` se for Gemini |

## Google APIs (Calendar + Docs + Drive)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GOOGLE_OAUTH_CLIENT_SECRETS_PATH` | sim | Caminho para o JSON do OAuth client (Calendar) ou da service account (Docs/Drive) |
| `GOOGLE_OAUTH_TOKEN_STORE_PATH` | sim | Diretório onde armazenar tokens OAuth dos alunos (criptografados) |
| `GOOGLE_DRIVE_KB_FOLDER_ID` | sim | ID da pasta no Drive que contém os docs da base de conhecimento |

Ver [[03-Integracoes/Google-Calendar]] e [[03-Integracoes/Google-Docs-Drive]].

## Sistema acadêmico

| Variável | Obrigatória | Descrição |
|---|---|---|
| `SISTEMA_ACADEMICO_BASE_URL` | sim | URL base da API da faculdade |
| `SISTEMA_ACADEMICO_API_KEY` | depende | Forma de autenticação a definir conforme [[03-Integracoes/Sistema-Academico]] |

## Observabilidade

| Variável | Obrigatória | Descrição |
|---|---|---|
| `LOG_LEVEL` | não | `DEBUG`, `INFO` (default), `WARNING`, `ERROR` |
| `LOG_FORMAT` | não | `json` (default) ou `text` |

Nota: estes controlam o log da **aplicação** (operacional), não o log de **interações** (que é o domínio de [[02-Dominios/Observabilidade]] e vai sempre para o banco).

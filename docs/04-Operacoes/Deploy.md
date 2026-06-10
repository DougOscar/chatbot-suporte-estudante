---
title: Deploy
tags: [operacoes, deploy]
---

# Deploy

## Modos de operação do bot

### Polling — recomendado em desenvolvimento

O processo do bot abre uma conexão com a API do Telegram e fica perguntando "tem mensagem nova?" em loop. Não precisa de domínio público nem HTTPS.

- **Prós**: zero infra, basta rodar o processo.
- **Contras**: 1 instância apenas (não escala horizontalmente sem orquestração extra), consumo constante mesmo sem tráfego.
- Configurado por `TELEGRAM_MODE=polling`.

### Webhook — recomendado em produção

O Telegram envia HTTP POST para uma URL nossa cada vez que chega uma mensagem.

- **Prós**: escala horizontalmente atrás de um load balancer; sem polling ocioso.
- **Contras**: precisa de **HTTPS válido** e domínio público; em hospedagens que "dormem" sem tráfego, a primeira mensagem após a inatividade demora.
- Configurado por `TELEGRAM_MODE=webhook` + `TELEGRAM_WEBHOOK_URL`.

## Componentes a hospedar

1. **Processo do bot** (polling ou webhook server)
2. **Postgres** (com `pgvector`)
3. **Job de sincronização da KB** (cron) — pode ser um cron do orquestrador ou um scheduler interno (APScheduler)

## Opções de hospedagem com tier gratuito

| Plataforma | O que cabe no free tier | Limitações relevantes |
|---|---|---|
| **Fly.io** | Pequenas VMs sempre ligadas; Postgres gerenciado tem versão paga apenas (usar Postgres em VM compartilhada ou externo) | Cartão de crédito requerido |
| **Railway** | $5 de crédito mensal (efetivamente free para projetos pequenos) | Sleeps após uso prolongado do crédito |
| **Render** | Free web service que **dorme** após inatividade + Postgres free 90 dias | Sleep faz a primeira mensagem demorar |
| **Oracle Cloud (Always Free)** | VMs ARM com bastante CPU/RAM permanentes | Curva de aprendizado de cloud "tradicional" |
| **PythonAnywhere** | Conta gratuita roda processos | Outbound de rede restrito a whitelist |
| **Supabase** | Postgres gerenciado free (500 MB, pgvector suportado) | Inativo por 1 semana → pausado |
| **Neon** | Postgres serverless free (3 GB, autoscale, pgvector) | Sem worker — só banco |

**Combinação sugerida para validação gratuita**: bot em **Fly.io** (VM pequena sempre ligada) + Postgres em **Neon** (free 3GB com pgvector).

## Variáveis essenciais em produção

Ver [[04-Operacoes/Variaveis-de-Ambiente]] — mínimo absoluto:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_MODE=webhook`
- `TELEGRAM_WEBHOOK_URL`
- `DATABASE_URL`
- `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`
- `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_API_KEY`
- `GOOGLE_OAUTH_CLIENT_SECRETS_PATH`, `GOOGLE_DRIVE_KB_FOLDER_ID`
- `SISTEMA_ACADEMICO_BASE_URL`, `SISTEMA_ACADEMICO_API_KEY`

## Job de sincronização da KB

Duas opções:
1. **Cron externo** (Fly cron, GitHub Actions agendado) executando `python -m scripts.sync_kb` periodicamente.
2. **Scheduler interno** (APScheduler) no mesmo processo do bot.

Recomendação: começar com cron externo — separa concerns, falha sem derrubar o bot.

## Health checks e prontidão

Quando em modo webhook, expor:
- `GET /healthz` — alive
- `GET /readyz` — pronto (banco respondendo, credenciais válidas)

## Deploy script (a definir)

Será adicionado quando houver `pyproject.toml` e Dockerfile. Esperado:
- `Dockerfile` multi-stage com base Python slim
- `docker-compose.yml` para desenvolvimento (bot + postgres + pgvector)
- Pipeline CI (GitHub Actions) para testes + build de imagem

→ [[04-Operacoes/Custos-e-Alternativas-Gratuitas]] | [[04-Operacoes/Banco-de-Dados]]

---
title: Custos e Alternativas Gratuitas
tags: [operacoes, custos]
---

# Custos & alternativas gratuitas

Catálogo dos componentes do sistema, identificando o que tem custo e quais são as alternativas free tier ou gratuitas.

## Resumo executivo

| Componente | Pago? | Substituto gratuito |
|---|---|---|
| Telegram Bot API | **Não** | — |
| Google Calendar API | **Não** (free tier amplo) | — |
| Google Docs + Drive API | **Não** (free tier amplo) | — |
| Service Account Google | **Não** | — |
| Postgres gerenciado | Depende | Neon (3 GB) ou Supabase (500 MB) free; ou self-hosted em VM |
| pgvector | **Não** (extensão open-source) | — |
| LLM (geração) | **Depende do provedor** | Gemini Flash free tier; Groq free tier; Ollama local |
| LLM (embeddings) | Depende | Gemini embedding free tier; ou `sentence-transformers` local |
| Hospedagem do bot | Depende | Fly.io / Railway / Render / Oracle Cloud free tiers |
| Domínio + HTTPS (webhook) | Pago (~$10/ano) | DuckDNS + Cloudflare Tunnel grátis para validação |

## Detalhe por componente

### LLM — onde o custo aparece de fato

Para um bot acadêmico com volume moderado (estimativa: ~500 mensagens/dia, ~600 tokens in + ~150 out por mensagem):

- **Volume mensal**: 15k mensagens × (600 + 150) = ~11M tokens/mês
- **Custo Gemini Flash**: ~$0.30 × 9M + $2.50 × 2.25M = **~$8/mês**
- **Custo Claude Haiku**: ~$1.00 × 9M + $5.00 × 2.25M = **~$20/mês**
- **Custo GPT-4o-mini**: ~$0.15 × 9M + $0.60 × 2.25M = **~$2.70/mês**

Em todos os casos, **o free tier do Gemini deve cobrir o uso de validação** (centenas de RPM gratuitas). Verificar limites atuais em https://ai.google.dev/pricing.

### Hospedagem — combinação 100% gratuita para validação

- **Bot**: Fly.io free tier (1 VM compartilhada `shared-cpu-1x` 256 MB) — suficiente para o processo Python.
- **Postgres**: Neon free (3 GB, pgvector incluso, autoscale).
- **Job de sync KB**: GitHub Actions agendado (cron) — 2.000 min/mês grátis em repos públicos.
- **Domínio (para webhook)**: DuckDNS (subdomínio grátis) + Cloudflare Tunnel para HTTPS sem comprar domínio.

### LLM local com Ollama

Se houver máquina com Apple Silicon ou GPU disponível:
- `ollama pull llama3.2:3b` ou `qwen2.5:7b`
- Custo: $0 em API; consumo de energia/hardware.
- Qualidade em pt-BR: razoável para perguntas simples; pode degradar em queries complexas.
- Latência: depende da máquina; M-series Apple ou GPU dedicada são confortáveis.

Útil para desenvolvimento offline e demos sem expor chave de API.

## Alertas de custo

- Configurar alertas de billing no Google Cloud Console (Calendar/Docs ficam sob mesmo projeto)
- Configurar alertas no provedor de LLM escolhido
- Métrica de custo estimado por dia derivada das interações registradas — query exemplo em [[02-Dominios/Observabilidade]]

## Decisão recomendada para o MVP

1. **Gemini Flash** como provedor de LLM e embeddings (free tier)
2. **Neon free** como banco
3. **Fly.io free** como host do bot (uma VM)
4. **GitHub Actions** para o cron de sync da KB

→ Custo total estimado de MVP: **$0/mês** dentro dos free tiers, escalando para algumas dezenas de USD quando passar dos limites.

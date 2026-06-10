---
title: Diagrama de Containers (C4 nível 2)
tags: [arquitetura, diagrama, c4]
---

# Diagrama de Containers

Visão interna do bot: principais componentes lógicos e como se comunicam.

```mermaid
flowchart TB
    subgraph ext[Externo]
        tg[Telegram Bot API]
        sa[Sistema Acadêmico]
        gcal[Google Calendar API]
        gdocs[Google Docs/Drive API]
        llm[Provedor de LLM]
    end

    subgraph entry[interfaces/telegram_bot]
        handlers[Handlers do Telegram<br/>comandos + mensagens livres]
    end

    subgraph app[application — casos de uso]
        uc_conv[Processar Mensagem]
        uc_matr[Consultar Matrícula]
        uc_fin[Consultar Pagamento]
        uc_cal[Consultar Calendário]
        uc_addgcal[Adicionar ao Google Calendar]
        uc_kb[Buscar na Base de Conhecimento]
        uc_log[Registrar Interação]
    end

    subgraph dom[domain — núcleo puro]
        bc_matr[Matrícula]
        bc_fin[Financeiro]
        bc_cal[Calendário]
        bc_kb[Conhecimento]
        bc_conv[Conversa<br/>+ intent routing]
        bc_obs[Observabilidade]
    end

    subgraph infra[infrastructure — adapters]
        ad_tg[Telegram adapter]
        ad_sa[Sistema Acadêmico HTTP client]
        ad_gcal[Google Calendar client]
        ad_gdocs[Google Docs/Drive client]
        ad_llm[LLM client]
        ad_db[(Postgres<br/>+ pgvector)]
    end

    tg <--> ad_tg --> handlers --> uc_conv
    uc_conv --> bc_conv
    bc_conv -.intenção.-> uc_matr & uc_fin & uc_cal & uc_kb & uc_addgcal
    uc_matr --> bc_matr --> ad_sa --> sa
    uc_fin --> bc_fin --> ad_sa
    uc_cal --> bc_cal --> ad_db
    uc_addgcal --> bc_cal --> ad_gcal --> gcal
    uc_kb --> bc_kb --> ad_db
    bc_kb -. sync periódica .- ad_gdocs --> gdocs
    uc_conv --> ad_llm --> llm
    uc_conv --> uc_log --> bc_obs --> ad_db
```

## Leitura

- **Setas cheias**: chamada síncrona durante o atendimento de uma mensagem.
- **Setas pontilhadas**: relação assíncrona ou esporádica (intent routing interno, sincronização periódica da KB).
- O **caso de uso "Processar Mensagem"** (`uc_conv`) é o orquestrador central — recebe a mensagem do handler, decide a intenção via [[02-Dominios/Conversa]], dispara os casos de uso pertinentes, monta o contexto, chama a LLM para formatar a resposta, e dispara o registro da interação.

## Pontos de extensão (ports principais)

| Port (no `domain`) | Adapter atual (em `infrastructure`) | Substituível por |
|---|---|---|
| `MatriculaRepository` | `infrastructure/sistema_academico` | Outro ERP / sistema acadêmico |
| `FinanceiroRepository` | `infrastructure/sistema_academico` | Idem |
| `CalendarioRepository` | `infrastructure/persistence` (Postgres) | Outro storage |
| `CalendarioExterno` | `infrastructure/google/calendar` | Outlook / Apple Calendar |
| `KbRepository` (vetor) | `infrastructure/persistence` (pgvector) | Qdrant / Pinecone / Chroma |
| `KbSyncSource` | `infrastructure/google/docs` | Notion / Confluence / arquivos locais |
| `LLMGateway` | `infrastructure/llm` | Qualquer outro provedor |
| `InteracaoLog` | `infrastructure/persistence` | Qualquer outro sink (ELK, BigQuery...) |

→ Fluxos detalhados em [[01-Arquitetura/Fluxos/Fluxo-Mensagem-Generico]]

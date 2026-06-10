---
title: Fluxo — FAQ / Base de Conhecimento (RAG)
tags: [fluxo, sequencia, rag, conhecimento]
---

# Fluxo — Base de conhecimento com RAG

Dois subfluxos: **ingestão** (offline, agendada) e **consulta** (online, durante a conversa).

## A) Ingestão — sincronização do Google Docs

Roda como job agendado (cron) ou comando manual (`scripts/sync_kb.py`).

```mermaid
sequenceDiagram
    autonumber
    participant Job as Sync KB Job
    participant Drive as Google Drive API
    participant Docs as Google Docs API
    participant Chunk as Chunker
    participant Embed as Embedding Provider
    participant DB as Postgres + pgvector

    Job->>Drive: list_files(folder=KB_FOLDER_ID)
    Drive-->>Job: [docId, modifiedTime, ...]
    loop para cada doc novo/modificado
        Job->>Docs: documents.get(docId)
        Docs-->>Job: conteúdo estruturado
        Job->>Chunk: dividir em chunks (~500-800 tokens)
        Chunk-->>Job: [chunks]
        Job->>Embed: embed_batch(chunks)
        Embed-->>Job: [vetores]
        Job->>DB: UPSERT kb_chunk (doc_id, chunk_idx, texto, vetor, doc_title, atualizado_em)
    end
```

## B) Consulta — RAG durante a conversa

```mermaid
sequenceDiagram
    autonumber
    actor Aluno
    participant UC as ProcessarMensagem
    participant Embed as Embedding Provider
    participant DB as Postgres + pgvector
    participant LLM
    participant LOG

    Aluno->>UC: "qual o prazo para trancamento?"
    UC->>Embed: embed(pergunta)
    Embed-->>UC: vetor_pergunta
    UC->>DB: SELECT ... ORDER BY embedding <=> vetor LIMIT 5
    DB-->>UC: top-k chunks relevantes
    UC->>LLM: gerar_resposta(intent=FAQ, chunks, pergunta)
    LLM-->>UC: resposta + citações
    UC->>LOG: registrar(msg, ctx={chunks_ids}, resp, tokens)
    UC-->>Aluno: resposta com referência ao doc
```

## Notas

- **Cache de embedding** da pergunta é opcional; perguntas repetidas se beneficiariam.
- O LLM recebe os chunks **citáveis** (com `doc_title`); a resposta deve incluir referência ("Conforme a política X, ...").
- **Limite de tokens de contexto**: se top-k for grande, truncar pelo orçamento do prompt — registrar quando isso ocorre.
- **Alucinação**: a instrução de sistema deve enfatizar "se a resposta não estiver nos trechos, diga que não sabe".
- **Reindexação**: chunks órfãos (docs deletados/movidos) devem ser limpos no job.

## Decisões pendentes

- **Estratégia de chunking**: por seção (header-based) é mais aderente a docs institucionais; fixed-size é mais simples. Decisão na primeira iteração.
- **Modelo de embedding**: ver comparativo em [[04-Operacoes/Custos-e-Alternativas-Gratuitas]].

→ [[02-Dominios/Conhecimento]] | [[03-Integracoes/Google-Docs-Drive]]

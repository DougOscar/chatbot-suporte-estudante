---
title: Domínio — Base de Conhecimento
tags: [dominio, bounded-context, rag]
---

# Conhecimento (Knowledge Base + RAG)

FAQs e políticas internas mantidas em **Google Docs**, sincronizadas para o banco e consultadas via **RAG** durante as conversas.

## Por que Google Docs como fonte?

- Pessoal não-técnico (secretaria acadêmica, coordenação) edita docs sem aprender ferramentas novas.
- Versionamento e permissionamento já existem.
- Drive API permite descobrir docs por pasta; Docs API extrai texto estruturado.

## Linguagem ubíqua

- **Documento KB** — um Google Doc dentro da pasta institucional designada (`GOOGLE_DRIVE_KB_FOLDER_ID`).
- **Chunk** — pedaço de texto (~500-800 tokens) com embedding associado, usado na busca semântica.
- **Top-k** — número de chunks mais relevantes recuperados por consulta (default sugerido: 5).

## Entidades

```
DocumentoKB
  - id                (google_doc_id)
  - titulo
  - url
  - atualizado_em_origem  (modifiedTime do Drive)
  - sincronizado_em
  - hash_conteudo     (para detectar mudanças)

ChunkKB
  - id
  - documento_id
  - indice            (ordem dentro do doc)
  - texto
  - embedding         (vector — pgvector)
  - criado_em
```

## Ports

- `KbRepository.buscar_por_similaridade(vetor, top_k) -> list[ChunkKB]`
- `KbRepository.upsert_chunks(documento_id, chunks)`
- `KbRepository.remover_documento(documento_id)`
- `KbSyncSource.listar_documentos() -> list[DocMetadata]`
- `KbSyncSource.carregar_texto(doc_id) -> str`
- `EmbeddingGateway.embed(texto) -> vector`
- `EmbeddingGateway.embed_batch(textos) -> list[vector]`

## Adapters

- `infrastructure/persistence` — pgvector via SQLAlchemy.
- `infrastructure/google/docs` — Drive + Docs API.
- `infrastructure/llm` — fornece também o embedding (ou um cliente dedicado).

## Estratégia de chunking — opções

| Estratégia | Prós | Contras |
|---|---|---|
| Por header (h1/h2/h3) | Respeita semântica do doc | Chunks de tamanho irregular |
| Fixed-size com overlap | Simples e previsível | Pode cortar no meio de ideias |
| Híbrida (header + split se >N tokens) | Melhor relação custo/qualidade | Mais complexa |

Recomendação: **híbrida**, começando simples (header-based) e medindo qualidade.

## Sincronização

- Rodada agendada (cron via [[04-Operacoes/Deploy]]) — sugestão: a cada 6h.
- Detecção de mudança por `modifiedTime` + hash do conteúdo.
- Docs removidos da pasta → chunks órfãos limpos.
- Comando admin `/scripts/sync_kb.py --force` para forçar reindexação completa.

## Casos de uso

- `BuscarConhecimento(pergunta, top_k=5) -> list[ChunkDTO]`
- `SincronizarKB() -> ResumoSync` (agendado / manual)

→ [[01-Arquitetura/Fluxos/Fluxo-FAQ-RAG]] | [[03-Integracoes/Google-Docs-Drive]]

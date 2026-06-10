---
title: Schema do Banco
tags: [modelagem, banco, postgres]
---

# Schema do Banco

Visão lógica das tabelas. Implementação real (Alembic + SQLAlchemy) deve seguir este desenho como referência.

## Diagrama de entidades

```mermaid
erDiagram
    aluno ||--o| matricula_cache : "tem"
    aluno ||--o{ oauth_google_token : "autoriza"
    aluno ||--o{ adicao_calendario_externo : "registra"
    aluno ||--o{ interacao : "produz"

    evento_calendario ||--o{ adicao_calendario_externo : "origina"

    documento_kb ||--o{ kb_chunk : "contém"

    aluno {
        uuid id PK
        bigint telegram_user_id UK
        text nome
        text email
        text matricula_id_externo
        timestamptz criado_em
        timestamptz atualizado_em
    }

    matricula_cache {
        uuid aluno_id PK_FK
        text status
        text curso
        smallint semestre_atual
        date desde
        timestamptz consultada_em
    }

    oauth_google_token {
        uuid id PK
        uuid aluno_id FK
        text provider "google"
        bytea access_token_cifrado
        bytea refresh_token_cifrado
        timestamptz expira_em
        timestamptz criado_em
    }

    evento_calendario {
        uuid id PK
        text titulo
        text descricao
        timestamptz inicio
        timestamptz fim
        boolean dia_inteiro
        text audiencia
        text local
        timestamptz criado_em
        timestamptz atualizado_em
    }

    adicao_calendario_externo {
        uuid id PK
        uuid aluno_id FK
        uuid evento_id FK
        text id_evento_google
        timestamptz adicionado_em
    }

    documento_kb {
        text id PK "google_doc_id"
        text titulo
        text url
        timestamptz atualizado_em_origem
        timestamptz sincronizado_em
        text hash_conteudo
    }

    kb_chunk {
        uuid id PK
        text documento_id FK
        integer indice
        text texto
        vector embedding "pgvector dim=768"
        timestamptz criado_em
    }

    interacao {
        uuid id PK
        uuid aluno_id FK "nullable"
        bigint telegram_user_id
        bigint chat_id
        text mensagem_recebida
        text intencao_detectada
        jsonb contexto_recuperado
        text resposta_enviada
        text llm_provider
        text llm_model
        text prompt_versao
        integer tokens_entrada
        integer tokens_saida
        integer latencia_ms
        text erro
        timestamptz criado_em
    }
```

## Notas por tabela

### `aluno`
- Identifica univocamente um aluno **dentro do bot** (UUID).
- `telegram_user_id` é único (cada conta Telegram = um aluno).
- `matricula_id_externo` é a chave usada nas chamadas ao sistema acadêmico.

### `matricula_cache`
- Cache opcional para reduzir chamadas ao sistema acadêmico.
- TTL via `consultada_em` + lógica de negócio em [[02-Dominios/Matricula]].

### `oauth_google_token`
- **Tokens cifrados em repouso** (chave de criptografia fora do banco, em variável de ambiente).
- Refresh token armazenado para renovar o access token automaticamente.

### `evento_calendario`
- Fonte de verdade do calendário acadêmico.
- `audiencia` é texto livre estruturado: `global`, `curso:ADM`, `semestre:5`, `turma:ADM-5A`. Decisão simples no MVP; pode virar tabela própria se evoluir.

### `adicao_calendario_externo`
- Registra o que cada aluno já adicionou ao Google Calendar dele.
- Usada para **deduplicação** (cliente clica 2x → não cria duas vezes).

### `documento_kb`
- `id` é o `google_doc_id` direto — não inventamos UUID.
- `hash_conteudo` permite detectar mudança mesmo quando `modifiedTime` é confiável demais.

### `kb_chunk`
- `embedding vector(768)` — dimensão depende do modelo de embedding (Gemini = 768; OpenAI small = 1536). Definir na migração.
- Índice HNSW para busca por similaridade:
  ```sql
  CREATE INDEX ON kb_chunk USING hnsw (embedding vector_cosine_ops);
  ```

### `interacao`
- **Tabela mais quente** do sistema — uma linha por mensagem respondida.
- `contexto_recuperado` em JSONB permite query estruturada (`->`, `->>`) sem schema rígido.
- Considerar particionamento por mês se o volume passar de ~1M linhas.

## Índices essenciais (além das PKs/FKs)

```sql
CREATE UNIQUE INDEX idx_aluno_telegram ON aluno (telegram_user_id);
CREATE INDEX idx_evento_inicio ON evento_calendario (inicio);
CREATE INDEX idx_evento_audiencia ON evento_calendario (audiencia);
CREATE INDEX idx_interacao_aluno_data ON interacao (aluno_id, criado_em DESC);
CREATE INDEX idx_interacao_data ON interacao (criado_em DESC);
CREATE INDEX idx_kb_chunk_hnsw ON kb_chunk USING hnsw (embedding vector_cosine_ops);
```

→ [[02-Dominios/Observabilidade]] | [[02-Dominios/Conhecimento]] | [[04-Operacoes/Banco-de-Dados]]

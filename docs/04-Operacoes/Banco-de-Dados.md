---
title: Banco de Dados
tags: [operacoes, banco, postgres, pgvector]
---

# Banco de Dados

**Postgres 16+** com extensão **`pgvector`** habilitada.

## Por que Postgres?

- Único banco para tudo: dados operacionais (alunos, eventos, tokens OAuth) + log de [[02-Dominios/Observabilidade|interações]] + vetores da [[02-Dominios/Conhecimento|base de conhecimento]].
- `pgvector` é estável, rápido e aceito em todos os provedores gerenciados relevantes (Supabase, Neon, Railway, RDS).
- Reduz superfície operacional (sem precisar de vector DB separado).

## Provisionamento local (desenvolvimento)

Sugestão usando Docker:

```bash
docker run -d --name chatbot-postgres \
  -e POSTGRES_USER=chatbot \
  -e POSTGRES_PASSWORD=chatbot \
  -e POSTGRES_DB=chatbot \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

A imagem `pgvector/pgvector:pg16` já vem com a extensão instalada — basta `CREATE EXTENSION vector` na migração inicial.

## Provisionamento em produção (free tier)

- **Neon** (https://neon.tech): free 3 GB, pgvector pré-disponível. Basta `CREATE EXTENSION vector` no banco.
- **Supabase** (https://supabase.com): free 500 MB, pgvector ativável no painel.

## Migrações

Ferramenta sugerida: **Alembic** (padrão SQLAlchemy).

Estrutura:
```
migrations/
├── env.py
├── script.py.mako
└── versions/
    └── <hash>_inicial.py    # cria tabelas + CREATE EXTENSION vector
```

Comandos esperados (vão para o README quando existirem):
- Aplicar todas: `alembic upgrade head`
- Criar nova: `alembic revision --autogenerate -m "<descrição>"`
- Voltar uma: `alembic downgrade -1`

## Schema

Schema completo, com índices e relacionamentos, em [[05-Modelagem/Schema-Banco]].

## Backups

- Em provedores gerenciados (Neon/Supabase), backup automático já existe.
- Em VM própria: `pg_dump` agendado via cron, despejado em bucket S3-compatível (B2/R2 têm free tier).

## Considerações de performance

- Índice HNSW em `kb_chunk.embedding` para busca vetorial (criado na migração).
- Particionamento por data em `interacao` se o volume crescer muito (decisão futura, registrar como ADR quando aplicável).
- Conexões: usar pool (SQLAlchemy default já faz). Em ambientes serverless considerar **PgBouncer**.

→ [[05-Modelagem/Schema-Banco]] | [[02-Dominios/Observabilidade]] | [[02-Dominios/Conhecimento]]

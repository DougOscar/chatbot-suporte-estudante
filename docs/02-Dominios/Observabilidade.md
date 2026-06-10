---
title: Domínio — Observabilidade
tags: [dominio, bounded-context, logging]
---

# Observabilidade

Captura **toda interação respondida pelo bot** com contexto, resposta e métricas. Persistido no mesmo Postgres da aplicação para permitir consultas analíticas.

## Por que é um domínio próprio?

- Tem regras próprias (o que registrar, como mascarar, retenção).
- Tem consumidores próprios (admins, dashboards, billing de tokens).
- Mantê-lo separado evita que cada caso de uso polua sua lógica com "como logar".

## Entidade central

```
Interacao
  - id
  - aluno_id            (nullable em casos de não-vinculados)
  - telegram_user_id
  - chat_id
  - mensagem_recebida
  - intencao_detectada
  - contexto_recuperado (JSONB)
  - resposta_enviada
  - llm_provider
  - llm_model
  - prompt_versao
  - tokens_entrada
  - tokens_saida
  - latencia_ms
  - erro                (nullable)
  - criado_em
```

Schema completo em [[05-Modelagem/Schema-Banco]].

## Ports

- `InteracaoLog.registrar(payload) -> id`

## Adapter

- `infrastructure/persistence` — INSERT direto na tabela `interacao`.
- (Futuro) Sinks adicionais possíveis: stdout JSON estruturado para coletor externo, BigQuery, ELK.

## Garantias e detalhes operacionais

- Registro **sempre** acontece — sucesso ou erro. Ver [[01-Arquitetura/Fluxos/Fluxo-Logging]].
- INSERT é feito em **background** (`asyncio.create_task`) para não bloquear a resposta ao aluno.
- Falha no INSERT → log de aplicação em `stderr` (JSON estruturado) + métrica. **Nunca** levantar exceção para o caller.

## Privacidade

- `contexto_recuperado` é JSON. **Considerar mascarar** valores monetários e PII conforme política a definir. Decisão pendente.
- `mensagem_recebida` é texto bruto do aluno — não tratado por enquanto.
- **Retenção**: política a definir (sugestão inicial: 12 meses para análise + agregados anonimizados perpétuos).

## Métricas derivadas (consultas SQL)

- **Custo estimado por aluno por mês**:
  `SUM(tokens_entrada × preco_in + tokens_saida × preco_out) GROUP BY aluno_id, mes`
- **Top intenções**: `COUNT(*) GROUP BY intencao_detectada ORDER BY 1 DESC`
- **Latência p95**: `percentile_cont(0.95) WITHIN GROUP (ORDER BY latencia_ms)`
- **Taxa de erro por integração**: derivada do campo `erro` parseado por categoria

## Casos de uso

- `RegistrarInteracao(payload)` — chamado pelo orquestrador de [[02-Dominios/Conversa]]

→ [[01-Arquitetura/Fluxos/Fluxo-Logging]] | [[05-Modelagem/Schema-Banco]]

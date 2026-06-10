---
title: Próximos passos / Roadmap
tags: [roadmap, pendencias, futuro]
---

# Próximos passos

Pendências identificadas durante as Fases 0-5 do MVP. Cada item descreve
**o estado atual**, **o que falta**, e **o que destrava**. Não é uma lista
de bugs — é o roteiro do próximo ciclo de produto/engenharia.

## 1. Onboarding aluno↔Telegram

**Hoje**: todo `telegram_user_id` é tratado como um aluno único — em
particular, os repositórios mock de Matrícula/Financeiro retornam sempre
o mesmo aluno fictício, e o storage OAuth faz UPSERT em `aluno` por
`telegram_user_id` (onboarding implícito). Decisão registrada em
[[02-Dominios/Matricula]] como pendência de produto.

**O que falta**:
- Definir o fluxo: 3 opções listadas no doc (token por e-mail/SMS,
  deep link via portal, OAuth do sistema acadêmico).
- Implementar `VincularContaTelegram(telegram_user_id, dados)` em
  `application/matricula`.
- Tabela `aluno.matricula_id_externo` é populada via fluxo de vínculo,
  não mais como side-effect do OAuth Google.
- Decisão arquitetural: o vínculo é pré-requisito (aluno só interage
  depois de vincular) ou opcional (intents públicas funcionam sem)?

**Bloqueador**: decisão de produto sobre o fluxo. Conversa com a
secretaria acadêmica.

## 2. API real do sistema acadêmico

**Hoje**: `infrastructure/sistema_academico/` tem só `MockMatriculaRepository`
e `MockFinanceiroRepository`. Flag `SISTEMA_ACADEMICO_MOCK=true` em dev.
Em produção, o composition root levanta `NotImplementedError`.

**O que falta**:
- Especificação da API real (endpoints, auth, formato dos status).
- Adapters HTTP `HttpMatriculaRepository` / `HttpFinanceiroRepository`
  com `httpx`, retry com backoff, timeouts agressivos (3-5s).
- Possível adoção de webhooks do sistema acadêmico para invalidar
  cache (`matricula_cache`) quando status mudam.
- Mapeamento dos valores reais de status para os valores canônicos
  documentados em [[05-Modelagem/Glossario-Ubiquo]].

**Bloqueador**: a faculdade definir e expor a API.

## 3. OAuth real do Google Calendar

**Hoje**: `MockOAuthClient` emula consent URL + troca de code; em produção
o composition root levanta `NotImplementedError`. O adapter real
`GoogleCalendarAdapter` (chamadas `events.insert`) **já está implementado**
e pronto para uso assim que houver token válido.

**O que falta**:
- Servidor HTTP para o callback OAuth (PTB v22 não expõe hook trivial
  para adicionar rotas custom no servidor de webhook — provável caminho:
  rodar um servidor `aiohttp`/`starlette` paralelo na mesma porta ou em
  outra, ou sidecar).
- Projeto Google Cloud configurado: OAuth consent screen (External),
  scope `calendar.events`, redirect URI público (`https://<bot>.tld/oauth/google/callback`).
- App em modo "Testing" → "Production" (verificação Google).
- Retirar o comando manual `/concluir_oauth <code>` (substituído pelo
  callback automático).

**Bloqueador**: decisão entre rodar HTTP server interno (acoplado ao bot)
vs. sidecar separado. Configurar projeto Google Cloud.

## 4. Source real do Google Docs/Drive (KB)

**Hoje**: `MockKbSource` com 4 documentos hardcoded. `scripts/sync_kb.py`
roda contra o mock se `GOOGLE_DRIVE_KB_FOLDER_ID` estiver vazio.

**O que falta**:
- Implementar `DriveKbSource` em `infrastructure/google/docs/`:
  - Service account autenticando via `service_account.Credentials`
  - `Drive.files.list` filtrando por `'<folder_id>' in parents and mimeType='application/vnd.google-apps.document'`
  - `Docs.documents.get(docId)` extraindo conteúdo estruturado
  - Conversão de estrutura (headers, listas, tabelas) → texto plano
- Service account criada no projeto Google Cloud, pasta da KB
  compartilhada com o e-mail da service account (`Viewer`).
- Setar `GOOGLE_DRIVE_KB_FOLDER_ID` no `.env`/secrets.
- Decisão de chunking final (header-based vs híbrido — ver
  [[02-Dominios/Conhecimento]]).
- Agendar `sync_kb.py` (sugestão: GitHub Actions agendado, a cada 6h).

**Bloqueador**: criar service account no Google Cloud e organizar a pasta
de documentos institucionais.

## 5. Política de PII e retenção em logs

**Hoje**: `interacao.contexto_recuperado` armazena JSON com todos os
dados que o LLM viu (matrícula, valores monetários, trechos da KB,
eventos). Sem mascaramento. Sem política de retenção implementada.

**O que falta**:
- Decisão de política: o que mascarar em `contexto_recuperado`?
  Candidatos óbvios: `pagamento.valor`, `pagamento.url_boleto`,
  `matricula.nome_aluno`. Decisão entre mascarar na escrita vs. armazenar
  cru e mascarar em queries analíticas.
- Decisão de retenção: a sugestão atual em
  [[02-Dominios/Observabilidade]] é "12 meses para análise + agregados
  anonimizados perpétuos". Confirmar com jurídico/compliance.
- Implementação: job de limpeza (`DELETE FROM interacao WHERE criado_em < now() - interval '12 months'`),
  view ou tabela de agregados que mantém métricas sem PII.

**Bloqueador**: decisão de compliance.

## 6. Healthcheck endpoints

**Hoje**: em modo webhook, o orquestrador (Fly/Cloud Run/etc.) faz TCP
check na porta — qualquer conexão aceita = saudável. Adequado para
liveness, fraco para readiness (não distingue "rodando" de "rodando mas
com banco fora").

**O que falta**:
- `GET /healthz` — liveness: retorna 200 se o processo está rodando.
- `GET /readyz` — readiness: testa conexão com banco (e talvez com a API
  do Telegram). Retorna 503 se algo crítico está fora.
- Decisão de implementação: PTB v22 expõe a aiohttp app interna do
  webhook? Sim, via `application.web_app` em versões recentes — vale
  verificar. Alternativa: sidecar com servidor HTTP dedicado.

**Bloqueador**: nenhum — pode ser implementado a qualquer momento.

## Melhorias incrementais identificadas

Pequenos itens que apareceram durante o MVP e ainda não foram tocados:

- **Refresh automático de tokens OAuth**: quando `expira_em` está
  próximo, refrescar antes de usar. Hoje o adapter usa o token cru sem
  checar validade.
- **Intent routing via LLM (Opção B)**: substituir as regras regex de
  `ClassificarIntencao` por structured output do LLM quando precisão
  ficar problemática. Decisão registrada em [[02-Dominios/Conversa]].
- **Histórico de conversa de N turnos**: hoje cada mensagem é stateless.
  Trade-off de tokens + privacidade.
- **Pre-commit hooks**: rodar ruff + mypy localmente antes do commit
  (atualmente só roda no CI).
- **`scripts/` no Docker image**: para rodar `seed_calendario` e
  `sync_kb` via `docker compose exec`. Hoje precisam rodar do host.
- **Pacote `chatbot` instalado não-editable no Dockerfile**: hoje `uv sync`
  no builder usa modo editable; para imagem de produção, idealmente
  `pip install dist/*.whl`.
- **Dimensão de embedding parametrizável**: hoje 768 (Gemini). Mudar
  exige migração — mas trocar `text-embedding-004` por OpenAI
  (1536-dim) requer migration que altera a coluna.
- **Sessões/estado por aluno**: `application.bot_data`/`user_data` do
  PTB poderia carregar `aluno_id` resolvido uma vez por interação em vez
  de descobrir toda hora.

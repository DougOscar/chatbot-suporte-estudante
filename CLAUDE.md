# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

Chatbot do Telegram para suporte ao estudante. Fachada conversacional sobre múltiplas integrações (sistema acadêmico, Google Calendar, Google Docs, LLM). Implementação Python.

**Estado atual**: scaffold completo de pastas e documentação — **nenhum código de aplicação ainda**. Toda a arquitetura está desenhada em [`docs/`](docs/) (vault Obsidian). O ponto de entrada da documentação é [`docs/00-Indice.md`](docs/00-Indice.md).

## Arquitetura — leia antes de implementar

Padrão escolhido: **Hexagonal (Ports & Adapters) + DDD tático leve**. ADR completo em [`docs/01-Arquitetura/Arquitetura-Hexagonal-DDD.md`](docs/01-Arquitetura/Arquitetura-Hexagonal-DDD.md).

Regras de dependência (**não violar sem ADR**):
- `domain/` não importa de `application/`, `infrastructure/` ou `interfaces/`
- `application/` importa apenas de `domain/`
- `infrastructure/` implementa ports definidos em `domain/`
- `interfaces/telegram_bot/` é o composition root (instancia adapters e injeta nos use cases)

Bounded contexts (um diretório por contexto em cada camada): `matricula`, `financeiro`, `calendario`, `conhecimento`, `conversa`, `observabilidade`. Cada um tem um doc em [`docs/02-Dominios/`](docs/02-Dominios/).

## Convenções obrigatórias

### Idioma — pt-BR para tudo versionado

- README, CHANGELOG, todo o conteúdo de `docs/`.
- Mensagens de commit, PRs, issues.
- Docstrings e comentários voltados a humanos.
- Identificadores de código (variáveis/funções/classes) ficam em inglês — convenção de linguagem.

### Configuração de Git (local, por repositório)

Antes do primeiro commit:

```bash
git config user.name "DougOscar"
git config user.email "DougOscar@users.noreply.github.com"
```

Confirmar com `git config --local --list`.

### Linguagem ubíqua

Termos de domínio (status de matrícula, status de pagamento, intenção, audiência, chunk, etc.) seguem o glossário em [`docs/05-Modelagem/Glossario-Ubiquo.md`](docs/05-Modelagem/Glossario-Ubiquo.md). Não criar sinônimos.

## Operações que exigem confirmação explícita do usuário

- Criar o repositório no GitHub (`gh repo create ... --public`) — uma vez público, é indexável.
- Primeiro `git push` para o remoto.
- Commitar qualquer coisa parecida com credencial (Telegram, Google, sistema acadêmico, LLM). O `.gitignore` já cobre os caminhos esperados; `.env` real **nunca** é commitado.

## Decisões de produto/técnicas já fixadas

- **Bot lib**: `python-telegram-bot` (assíncrono).
- **Banco**: Postgres + `pgvector` (vetores no mesmo banco — sem vector DB separado).
- **LLM provedor**: configurável via `LLM_PROVIDER`; default sugerido para dev/MVP é **Gemini Flash** (free tier). Comparativo em [`docs/03-Integracoes/LLM-Provedores.md`](docs/03-Integracoes/LLM-Provedores.md).
- **Google Calendar**: OAuth **por aluno** (scope `calendar.events`).
- **Google Docs/Drive (KB)**: **service account** com permissão Viewer na pasta da KB.
- **Logging de interações**: tabela `interacao` no Postgres com tokens in/out, contexto recuperado em JSONB, registro em background (`asyncio.create_task`) para não bloquear resposta. Schema em [`docs/05-Modelagem/Schema-Banco.md`](docs/05-Modelagem/Schema-Banco.md).

## Comandos comuns

Gerenciador de pacotes: **uv**. Python pinado em `.python-version` (3.12). Lockfile `uv.lock` é versionado.

```bash
uv sync                            # instala/atualiza dependências a partir de uv.lock
uv sync --extra gemini             # inclui SDK do provedor de LLM (gemini|anthropic|openai|groq|local-embeddings)
uv add <pacote>                    # adiciona dep runtime
uv add --group dev <pacote>        # adiciona dep de dev (ruff/mypy/pytest)
uv run ruff check .                # lint
uv run ruff check --fix .          # lint + auto-fix
uv run ruff format .               # format
uv run mypy src                    # type check (strict)
uv run pytest                      # roda testes
uv run pytest tests/unit/test_x.py::test_y   # um teste específico
uv run pytest -m unit              # apenas testes marcados como `unit`
```

Markers de pytest disponíveis (definidos em `pyproject.toml`): `unit`, `integration`, `e2e`.

### Migrações (Alembic)

```bash
uv run alembic upgrade head                                  # aplica migrações
uv run alembic upgrade head --sql                            # gera SQL offline (não conecta)
uv run alembic downgrade -1                                  # volta uma versão
uv run alembic revision --autogenerate -m "<descrição>"      # cria nova (precisa de DB)
uv run alembic history                                       # lista versões
uv run alembic current                                       # versão atual no DB
```

Notas importantes:
- `migrations/env.py` lê **apenas** `DATABASE_URL` (via `DatabaseSettings()` direto, não `get_settings()`) — o Alembic roda sem precisar das demais variáveis de ambiente configuradas.
- A migração inicial cria a extensão `pgvector` e o índice **HNSW** em `kb_chunk.embedding`. Requer Postgres com extensão `vector` >= 0.5 (a imagem `pgvector/pgvector:pg16` atende).
- A dimensão do vetor é **768** (Gemini `text-embedding-004`). Mudar exige nova migração — `EMBEDDING_DIM` precisa bater entre `models.py` e a migração.

### Rodar o bot localmente

Pré-requisitos: Postgres rodando (container `chatbot-postgres` na :5433 ou outro), `.env` preenchido com `TELEGRAM_BOT_TOKEN` válido, migrações aplicadas.

```bash
uv run chatbot-bot                                  # entry point CLI
# ou equivalente:
uv run python -m chatbot.interfaces.telegram_bot
```

O processo conecta no Telegram em **polling**, registra cada interação na tabela `interacao`, e segue rodando até `Ctrl+C`. Em modo webhook (`TELEGRAM_MODE=webhook`) ainda não há suporte — vai virar `NotImplementedError`.

### Seed de dados de exemplo

```bash
uv run python scripts/seed_calendario.py     # ~15 eventos no banco (idempotente)
```

### Provedor de LLM

Default: **Gemini Flash** via SDK `google-genai` (já incluído no grupo `dev`).
- Sem `LLM_API_KEY` no `.env`: bot sobe normalmente e responde com `NullLLMGateway` (mensagem fixa "ainda não configurado"). Calendário continua funcionando porque é interno.
- Com `LLM_API_KEY`: respostas geradas por Gemini Flash, tokens contabilizados em `interacao.tokens_entrada/saida`.

Para trocar de provedor: implementar adapter em `infrastructure/llm/<provedor>_gateway.py` e adicionar branch em `_construir_gateway_llm` no entry point. Mudar `LLM_PROVIDER` no `.env`. SDKs alternativos são extras: `uv sync --extra anthropic|openai|groq`.

### Persona / prompt

Definida em `src/chatbot/domain/conversa/persona.py` como `PERSONA_PADRAO`. Mudar texto = bumpar `versao` (campo `prompt_versao` em `interacao` permite correlacionar mudanças de tom com métricas).

### Sistema Acadêmico (mock)

A API real do sistema acadêmico não está definida ainda. Em dev usar `SISTEMA_ACADEMICO_MOCK=true` no `.env` — repositórios em `infrastructure/sistema_academico/mock_*` retornam dados fictícios de um aluno único, independente do `telegram_user_id`. Quando a API real existir, criar adapter HTTP (`infrastructure/sistema_academico/http_*`) e mudar para `mock=false`.

**Limitação documentada**: sem onboarding aluno↔Telegram, **todo usuário do Telegram vê o mesmo aluno fictício**. Resolver quando o fluxo de vínculo for implementado (ver `docs/02-Dominios/Matricula.md`).

## A preencher quando o código existir

Estes itens **ainda não têm comandos reais** — adicionar aqui quando forem criados, **sem inventar antes**:

- Comando para rodar o job de sincronização da KB (provável `uv run python -m scripts.sync_kb`).
- Dockerfile / docker-compose para dev.

Estrutura de pastas existente:
```
src/chatbot/{domain,application,infrastructure,interfaces}/
tests/{unit,integration,e2e}/
migrations/
scripts/
docs/   ← vault Obsidian
```

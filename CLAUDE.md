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

## A preencher quando o código existir

Estes itens **ainda não têm comandos reais** — adicionar aqui quando forem criados, **sem inventar antes**:

- Comando para rodar o bot localmente em polling (será algo como `uv run python -m chatbot` após criarmos o entry point).
- Comando para aplicar migrações (provável `uv run alembic upgrade head`).
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

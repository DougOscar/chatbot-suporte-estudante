# Chatbot de Suporte ao Estudante

Bot do Telegram que ajuda alunos a consultarem sua situação acadêmica (matrícula, pagamentos, calendário) e a obterem respostas baseadas em uma base de conhecimento institucional. Usa LLM para gerar respostas curtas e conversacionais a partir do contexto recuperado das integrações.

> **Status**: projeto em fase de planejamento/scaffold. Ainda não há código de aplicação — apenas estrutura de pastas, configuração e documentação. Veja `docs/` (vault Obsidian) para o desenho completo da arquitetura.

---

## Funcionalidades planejadas

- Consulta de **status de matrícula** (matriculado, trancado, formado, etc.).
- Consulta do **próximo pagamento** com data de vencimento e link para o boleto/arquivo.
- Consulta ao **calendário acadêmico interno** (eventos armazenados no banco).
- **Adicionar evento ao Google Calendar** do aluno com um toque.
- **Base de conhecimento** sincronizada a partir de Google Docs (FAQs e políticas internas), consultada via RAG.
- Respostas **conversacionais geradas por LLM**, usando o contexto recuperado das integrações.
- **Log completo** de cada interação: mensagem do usuário, contexto recuperado, resposta, timestamp, tokens consumidos (entrada e saída). Tudo persistido em banco.

Detalhes de cada feature: [[docs/02-Dominios/]] no vault.

---

## Stack

- **Linguagem**: Python (3.12+ sugerido)
- **Bot**: [`python-telegram-bot`](https://python-telegram-bot.org/) (assíncrono, MIT)
- **Banco**: PostgreSQL (com extensão **pgvector** para o RAG)
- **LLM**: provedor configurável — padrão sugerido para dev é **Gemini free tier** ou **Groq free tier**; produção pode usar Claude Haiku/Sonnet ou GPT-4o-mini. Ver `docs/04-Operacoes/Custos-e-Alternativas-Gratuitas.md`.
- **Integrações Google**: Calendar API + Docs API + Drive API (todas gratuitas dentro de quotas)
- **Documentação**: Vault Obsidian em `docs/`

---

## Pré-requisitos

- Python 3.12 ou superior
- PostgreSQL 16+ com extensão `pgvector` instalada
- Conta no Telegram (para criar o bot via [@BotFather](https://t.me/BotFather))
- Conta Google com projeto no Google Cloud Console (para Calendar e Docs)
- Chave de API do provedor de LLM escolhido
- Obsidian (opcional, recomendado para ler/editar `docs/`)

---

## Configuração local

> Comandos exatos de instalação/execução serão preenchidos quando o `pyproject.toml` e o entrypoint do bot existirem. Esta seção fixa **o roteiro de configuração** que precisa estar pronto antes de rodar.

1. **Clonar o repositório**
   ```bash
   git clone https://github.com/DougOscar/<nome-do-repo>.git
   cd <nome-do-repo>
   ```

2. **Configurar autoria local de git** (apenas neste repositório)
   ```bash
   git config user.name "DougOscar"
   git config user.email "DougOscar@users.noreply.github.com"
   ```

3. **Copiar e preencher variáveis de ambiente**
   ```bash
   cp .env.example .env
   ```
   Cada variável está documentada em [`docs/04-Operacoes/Variaveis-de-Ambiente.md`](docs/04-Operacoes/Variaveis-de-Ambiente.md).

4. **Criar o bot no Telegram**
   Siga o passo a passo em [`docs/03-Integracoes/Telegram-BotFather.md`](docs/03-Integracoes/Telegram-BotFather.md).
   O token gerado vai em `TELEGRAM_BOT_TOKEN` no `.env`.

5. **Configurar credenciais Google (Calendar + Docs + Drive)**
   Passo a passo em [`docs/03-Integracoes/Google-Calendar.md`](docs/03-Integracoes/Google-Calendar.md) e [`docs/03-Integracoes/Google-Docs-Drive.md`](docs/03-Integracoes/Google-Docs-Drive.md).

6. **Provisionar banco e rodar migrações**
   Instruções em [`docs/04-Operacoes/Banco-de-Dados.md`](docs/04-Operacoes/Banco-de-Dados.md) (incluindo como habilitar `pgvector`).

7. **Subir o bot** (modo polling para desenvolvimento)
   O comando exato será adicionado aqui após a primeira iteração de código.

---

## Deploy

Opções de hospedagem com tier gratuito estão catalogadas em [`docs/04-Operacoes/Deploy.md`](docs/04-Operacoes/Deploy.md) e [`docs/04-Operacoes/Custos-e-Alternativas-Gratuitas.md`](docs/04-Operacoes/Custos-e-Alternativas-Gratuitas.md).

Em produção o bot opera em modo **webhook**; em desenvolvimento, em **polling**. Detalhes do trade-off também no documento de deploy.

---

## Estrutura de pastas

```
.
├── docs/                    Vault Obsidian (documentação completa)
├── src/chatbot/
│   ├── domain/              Núcleo puro — entidades, regras, contratos (ports)
│   ├── application/         Casos de uso (orquestração entre domínios)
│   ├── infrastructure/      Adapters: Telegram, Google, LLM, banco, sistema acadêmico
│   └── interfaces/          Entry points (telegram_bot é o composition root)
├── tests/                   unit / integration / e2e
├── migrations/              Migrações do banco
└── scripts/                 Utilitários (seed, sincronização da KB, etc.)
```

Justificativa da arquitetura (Hexagonal + DDD leve): [`docs/01-Arquitetura/Arquitetura-Hexagonal-DDD.md`](docs/01-Arquitetura/Arquitetura-Hexagonal-DDD.md).

---

## Documentação completa (Obsidian)

Toda a documentação técnica está em [`docs/`](docs/) e foi escrita para ser aberta como **vault do Obsidian**:

1. Abra o Obsidian → **Open folder as vault** → selecione a pasta `docs/`.
2. Comece pelo arquivo [`00-Indice.md`](docs/00-Indice.md).
3. Pressione `Ctrl/Cmd + G` para ver o grafo de relacionamentos entre documentos.

Os diagramas usam **Mermaid** (renderização nativa do Obsidian — nenhum plugin necessário).

---

## Licença

A definir.

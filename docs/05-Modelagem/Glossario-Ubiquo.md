---
title: Glossário (linguagem ubíqua)
tags: [modelagem, glossario, ddd]
---

# Glossário — Linguagem Ubíqua

Termos do domínio usados de forma consistente em código, documentação e conversas com stakeholders. Versionar este arquivo é obrigatório quando um termo muda.

## Aluno

Pessoa física com vínculo (atual ou histórico) com a instituição. Identificada no bot por `telegram_user_id` e mapeada para um `matricula_id_externo` do sistema acadêmico.

## Matrícula

Vínculo formal de um aluno com um curso em um período. Domínio em [[02-Dominios/Matricula]].

### Status de matrícula

- **ATIVA** — aluno regularmente matriculado, frequentando.
- **TRANCADA** — aluno suspendeu temporariamente o curso (com retorno previsto).
- **CANCELADA** — vínculo encerrado pelo aluno ou pela instituição.
- **FORMADO** — aluno concluiu o curso.
- **INADIMPLENTE** — vínculo ativo, mas com pendências financeiras que bloqueiam serviços.

> Esses valores devem ser confirmados com a equipe da faculdade — ver [[03-Integracoes/Sistema-Academico]].

## Pagamento

Cobrança específica direcionada a um aluno (mensalidade, taxa, multa). Domínio em [[02-Dominios/Financeiro]].

### Status de pagamento

- **EM_ABERTO** — emitido, ainda não pago, dentro do prazo.
- **PAGO** — quitado.
- **VENCIDO** — passou do prazo sem quitação.
- **EM_NEGOCIACAO** — acordo de pagamento em andamento.

## Próximo pagamento

O pagamento `EM_ABERTO` ou `VENCIDO` mais próximo do `vencimento`. É o que respondemos quando o aluno pergunta "quando vence?".

## Evento de calendário

Entrada institucional com data (ou intervalo), título, descrição, e audiência. Domínio em [[02-Dominios/Calendario]].

## Audiência

Para quem o evento se aplica. Valores possíveis:
- `global` — todos os alunos
- `curso:<sigla>` — alunos do curso
- `semestre:<N>` — alunos do semestre N
- `turma:<id>` — alunos de uma turma específica

## Calendário interno vs. externo

- **Calendário interno** — banco do bot (fonte de verdade).
- **Calendário externo** — Google Calendar do aluno (destino opcional de "adicionar").

## Documento KB

Um Google Doc dentro da pasta institucional designada (`GOOGLE_DRIVE_KB_FOLDER_ID`). Domínio em [[02-Dominios/Conhecimento]].

## Chunk

Pedaço de texto de um Documento KB (~500-800 tokens), com embedding associado. Unidade de recuperação no RAG.

## Top-k

Quantidade de chunks mais relevantes recuperados para uma pergunta (default sugerido: 5).

## Intenção

Categoria semântica da mensagem do aluno, determinada pelo intent router. Valores: `MATRICULA`, `PROXIMO_PAGAMENTO`, `PAGAMENTOS_LISTAR`, `CALENDARIO`, `ADD_GCAL`, `FAQ`, `SAUDACAO`, `INDEFINIDO`.

## Persona

Conjunto de instruções fixas no prompt de sistema que definem o tom do bot. Versionada (`prompt_versao` na tabela `interacao`).

## Interação

Uma mensagem do aluno e a resposta correspondente do bot, com todo o contexto recuperado, tokens consumidos e metadados. Persistida na tabela `interacao`. Ver [[02-Dominios/Observabilidade]].

## LLM Gateway

Port no domínio de [[02-Dominios/Conversa]] que abstrai o provedor de LLM concreto. Permite trocar Gemini ↔ Claude ↔ OpenAI ↔ Groq ↔ Ollama sem mexer no domínio.

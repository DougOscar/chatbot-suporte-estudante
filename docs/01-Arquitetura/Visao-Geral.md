---
title: Visão Geral da Arquitetura
tags: [arquitetura, visao-geral]
---

# Visão Geral

O sistema é um **bot do Telegram** que atua como uma **fachada conversacional** sobre múltiplas fontes de dados institucionais. O aluno conversa em linguagem natural; o bot identifica a intenção, recupera o contexto relevante de uma ou mais integrações, e responde com texto curto gerado por LLM.

## Princípios de design

1. **A LLM nunca é fonte de verdade.** Dados sensíveis (matrícula, pagamentos, calendário) vêm sempre de APIs autoritativas. A LLM apenas formata/conversa.
2. **Cada integração externa é um adapter substituível** (princípio da Arquitetura Hexagonal). Trocar provedor de LLM, banco ou sistema acadêmico não deve tocar o domínio.
3. **Bounded contexts isolados.** Matrícula não conhece Financeiro; ambos publicam contratos consumidos pelo domínio de [[02-Dominios/Conversa|Conversa]].
4. **Observabilidade é cidadã de primeira classe.** Toda interação é registrada com contexto recuperado e tokens consumidos — ver [[02-Dominios/Observabilidade]].
5. **Privacidade por padrão.** Dados pessoais não saem dos logs em texto plano legível por terceiros; pseudonimização quando aplicável.

## Atores e fontes de dados

- **Aluno** → conversa pelo Telegram
- **Sistema acadêmico da faculdade** → fonte autoritativa de matrícula e pagamentos
- **Banco interno (Postgres)** → calendário acadêmico, base de conhecimento indexada (pgvector), histórico de conversas, logs
- **Google Calendar** → destino do "Adicionar ao calendário"
- **Google Docs + Drive** → fonte da base de conhecimento (FAQs/políticas)
- **Provedor de LLM** → geração de respostas curtas em pt-BR

Ver o diagrama completo em [[01-Arquitetura/Diagrama-Contexto]] e [[01-Arquitetura/Diagrama-Containers]].

## Decisão arquitetural central

→ [[01-Arquitetura/Arquitetura-Hexagonal-DDD]]

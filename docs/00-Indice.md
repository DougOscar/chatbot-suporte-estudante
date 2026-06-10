---
title: Índice do Vault
tags: [indice, navegacao]
---

# Índice — Chatbot de Suporte ao Estudante

Vault Obsidian com o desenho técnico completo do bot. Abra esta pasta como vault (**Open folder as vault** no Obsidian) e use `Ctrl/Cmd + G` para visualizar o grafo de relacionamentos.

## 01 — Arquitetura

- [[01-Arquitetura/Visao-Geral]] — visão executiva, o que é o sistema
- [[01-Arquitetura/Arquitetura-Hexagonal-DDD]] — ADR explicando a escolha
- [[01-Arquitetura/Diagrama-Contexto]] — C4 nível 1 (sistema e atores externos)
- [[01-Arquitetura/Diagrama-Containers]] — C4 nível 2 (componentes internos)
- Fluxos ponta-a-ponta:
  - [[01-Arquitetura/Fluxos/Fluxo-Mensagem-Generico]]
  - [[01-Arquitetura/Fluxos/Fluxo-Matricula]]
  - [[01-Arquitetura/Fluxos/Fluxo-Pagamentos]]
  - [[01-Arquitetura/Fluxos/Fluxo-Calendario]]
  - [[01-Arquitetura/Fluxos/Fluxo-FAQ-RAG]]
  - [[01-Arquitetura/Fluxos/Fluxo-Logging]]

## 02 — Domínios (bounded contexts)

- [[02-Dominios/Matricula]]
- [[02-Dominios/Financeiro]]
- [[02-Dominios/Calendario]]
- [[02-Dominios/Conhecimento]]
- [[02-Dominios/Conversa]]
- [[02-Dominios/Observabilidade]]

## 03 — Integrações externas

- [[03-Integracoes/Telegram-BotFather]] — como criar o bot e obter o token
- [[03-Integracoes/Google-Calendar]] — OAuth e API de Calendar
- [[03-Integracoes/Google-Docs-Drive]] — sincronização da base de conhecimento
- [[03-Integracoes/LLM-Provedores]] — comparativo de provedores e configuração
- [[03-Integracoes/Sistema-Academico]] — integração com a API da faculdade

## 04 — Operações

- [[04-Operacoes/Deploy]] — modos de operação (polling/webhook) e hospedagem
- [[04-Operacoes/Variaveis-de-Ambiente]] — referência completa do `.env`
- [[04-Operacoes/Banco-de-Dados]] — Postgres + pgvector, migrações
- [[04-Operacoes/Custos-e-Alternativas-Gratuitas]] — APIs pagas e substitutos gratuitos

## 05 — Modelagem

- [[05-Modelagem/Schema-Banco]] — tabelas e relacionamentos
- [[05-Modelagem/Glossario-Ubiquo]] — termos do domínio (linguagem ubíqua)

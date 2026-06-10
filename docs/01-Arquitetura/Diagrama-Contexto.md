---
title: Diagrama de Contexto (C4 nível 1)
tags: [arquitetura, diagrama, c4]
---

# Diagrama de Contexto

Visão de mais alto nível: o bot como uma caixa preta e seus relacionamentos com atores externos.

```mermaid
flowchart LR
    aluno([Aluno])
    bot[Chatbot de Suporte<br/>ao Estudante]
    telegram[(Telegram<br/>Bot API)]
    sa[(Sistema Acadêmico<br/>da Faculdade)]
    gcal[(Google Calendar)]
    gdocs[(Google Docs + Drive)]
    llm[(Provedor de LLM)]

    aluno -- "mensagens em<br/>linguagem natural" --> telegram
    telegram <-- "updates / replies" --> bot
    bot -- "consulta matrícula<br/>e pagamentos" --> sa
    bot -- "cria eventos no<br/>calendário do aluno" --> gcal
    bot -- "sincroniza FAQs<br/>e políticas" --> gdocs
    bot -- "gera resposta<br/>conversacional" --> llm
```

## Relações com bounded contexts

- **Telegram** → entrada/saída, atendida por [[02-Dominios/Conversa]]
- **Sistema Acadêmico** → fonte de [[02-Dominios/Matricula]] e [[02-Dominios/Financeiro]]
- **Google Calendar** → destino de "add to calendar" em [[02-Dominios/Calendario]]
- **Google Docs/Drive** → fonte da [[02-Dominios/Conhecimento]]
- **LLM** → motor de geração usado pela [[02-Dominios/Conversa]]
- Toda interação é registrada por [[02-Dominios/Observabilidade]]

→ Detalhe interno: [[01-Arquitetura/Diagrama-Containers]]

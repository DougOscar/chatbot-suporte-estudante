---
title: ADR — Arquitetura Hexagonal + DDD leve
tags: [arquitetura, adr, decisao]
---

# ADR: Arquitetura Hexagonal (Ports & Adapters) com DDD tático leve

**Status**: Aceito
**Data**: 2026-06-09

## Contexto

O bot é, na essência, uma fachada conversacional sobre várias APIs externas (Telegram, Google Calendar, Google Docs, sistema acadêmico, provedor de LLM). Cada integração tem ciclo de vida próprio: o sistema acadêmico pode ser trocado/atualizado, queremos liberdade para mudar de provedor de LLM, e o canal hoje é Telegram mas pode ganhar WhatsApp/web no futuro.

## Decisão

Adotar **Arquitetura Hexagonal (Ports & Adapters)** como esqueleto, com **patterns táticos do DDD** aplicados de forma leve dentro de cada bounded context. Não adotamos DDD estratégico completo (sem event sourcing, sem CQRS, sem sagas distribuídas).

### Como isso se materializa

```
src/chatbot/
├── domain/                   <-- núcleo puro (sem deps externas)
│   ├── matricula/            <-- bounded context: entidades, value objects, ports
│   ├── financeiro/
│   ├── calendario/
│   ├── conhecimento/
│   ├── conversa/             <-- orquestrador conversacional
│   └── observabilidade/
├── application/              <-- casos de uso (orquestram ports)
│   └── ... (mesmos contextos)
├── infrastructure/           <-- adapters (implementam ports)
│   ├── persistence/          <-- SQLAlchemy, repositórios concretos
│   ├── telegram/             <-- handlers do python-telegram-bot
│   ├── llm/                  <-- cliente de LLM (Gemini/Anthropic/OpenAI/...)
│   ├── google/calendar/
│   ├── google/docs/
│   ├── sistema_academico/    <-- HTTP client da API da faculdade
│   └── observabilidade/      <-- writer de logs estruturados
└── interfaces/
    └── telegram_bot/         <-- composition root (entry point)
```

### Regras de dependência

- `domain` **não importa** de `application`, `infrastructure` ou `interfaces`.
- `application` importa apenas de `domain`.
- `infrastructure` importa de `domain` (para implementar ports) e às vezes de `application` (DTOs).
- `interfaces` é o **composition root**: instancia adapters concretos e injeta em casos de uso.
- Cada bounded context expõe **ports** (interfaces/Protocol) no `domain`; adapters concretos vivem em `infrastructure`.

### DDD leve — o que mantemos

- **Linguagem ubíqua** (ver [[05-Modelagem/Glossario-Ubiquo]])
- **Bounded contexts** explícitos (um diretório por contexto em cada camada)
- **Entidades** e **value objects** quando agregam invariantes
- **Repositories** como ports

### O que deixamos de fora (deliberadamente)

- Event sourcing
- CQRS
- Domain events publicados em bus assíncrono (usaremos chamada direta entre use cases quando preciso)
- Aggregates "puros" no sentido de Vernon — entidades são "anêmicas o suficiente" para um sistema desse porte

## Consequências

**Positivas**:
- Trocar provedor de LLM = trocar um adapter
- Trocar Telegram por outro canal = adicionar um novo entry point sem mexer no domínio
- Testes unitários de domínio rodam sem rede, sem banco, sem mocks pesados
- Contextos isolados evitam acoplamento acidental entre Matrícula, Financeiro etc.

**Negativas / custos**:
- Boilerplate de ports + adapters cresce com o tempo
- Para um projeto muito pequeno isso seria over-engineering; aqui o número de integrações justifica
- Curva de aprendizado maior para quem nunca viu hexagonal

## Alternativas consideradas

- **Arquitetura em camadas tradicional (3-tier)**: descartada porque amarra o domínio às escolhas de framework
- **DDD completo com event sourcing**: descartado por excesso de cerimônia para um chatbot
- **Monolito flat estilo "scripts + handlers"**: simples no curto prazo, mas dificulta trocar LLM/canal/banco

## Referências cruzadas

- [[01-Arquitetura/Visao-Geral]]
- [[01-Arquitetura/Diagrama-Containers]]
- Cada [[02-Dominios|bounded context]]

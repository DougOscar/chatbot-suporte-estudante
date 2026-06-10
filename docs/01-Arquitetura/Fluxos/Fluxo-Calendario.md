---
title: Fluxo — Calendário e "Adicionar ao Google Calendar"
tags: [fluxo, sequencia, calendario]
---

# Fluxo — Calendário e "Adicionar ao Google Calendar"

São dois subfluxos relacionados:

## A) Consultar próximos eventos do calendário acadêmico

```mermaid
sequenceDiagram
    autonumber
    actor Aluno
    participant H as Handler
    participant UC as ConsultarCalendario
    participant Repo as CalendarioRepository
    participant DB as Postgres
    participant LLM
    participant LOG

    Aluno->>H: "quais as próximas datas importantes?"
    H->>UC: ConsultarCalendario(usuario, horizonte=30d)
    UC->>Repo: proximos_eventos(curso_id, 30d)
    Repo->>DB: SELECT * FROM evento_calendario WHERE ...
    DB-->>Repo: [eventos]
    Repo-->>UC: [EventoDTO]
    UC->>LLM: gerar_resposta(intent=CALENDARIO, eventos)
    LLM-->>UC: resposta resumida
    UC->>LOG: registrar(...)
    UC-->>H: resposta + botões "Adicionar ao Google Calendar" por evento
```

## B) Adicionar evento ao Google Calendar do aluno

Acionado quando o aluno clica num botão inline com `callback_data` referenciando um `evento_id`.

```mermaid
sequenceDiagram
    autonumber
    actor Aluno
    participant H as CallbackHandler
    participant UC as AdicionarAoGoogleCalendar
    participant Auth as Google OAuth Store
    participant GCal as Google Calendar API
    participant LOG

    Aluno->>H: clica "Adicionar"
    H->>UC: AdicionarAoGoogleCalendar(usuario, evento_id)
    UC->>Auth: token_para(usuario)
    alt sem token
        Auth-->>UC: ausente
        UC-->>H: link OAuth (consent screen)
        H->>Aluno: "autorize aqui: <link>"
        Note over Aluno,Auth: aluno autoriza no browser, token salvo
    else token presente
        Auth-->>UC: access_token (refresh se preciso)
        UC->>GCal: events.insert(...)
        GCal-->>UC: 200 OK
        UC->>LOG: registrar(...)
        UC-->>H: "evento adicionado ✓"
        H->>Aluno: confirmação
    end
```

## Notas

- A **fonte de verdade do calendário** é o banco interno (todos os eventos institucionais são cadastrados lá). O Google Calendar é apenas destino opcional, por solicitação do aluno.
- O **OAuth do Google é por aluno**: cada usuário do bot precisa autorizar uma vez. O token (com refresh) é armazenado criptografado no banco. Ver [[03-Integracoes/Google-Calendar]].
- Eventos enviados ao Google Calendar incluem `extendedProperties.private.bot_evento_id` para deduplicação caso o aluno clique duas vezes.

→ [[02-Dominios/Calendario]] | [[03-Integracoes/Google-Calendar]]

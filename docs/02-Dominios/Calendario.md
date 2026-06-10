---
title: Domínio — Calendário
tags: [dominio, bounded-context]
---

# Calendário

Eventos acadêmicos institucionais (datas de prova, períodos de matrícula, recesso, eventos de curso) e a ponte com o **Google Calendar do aluno**.

## Linguagem ubíqua

- **Evento de calendário** — entrada institucional com data (ou intervalo), título, descrição, audiência (curso/semestre/global).
- **Calendário interno** — fonte de verdade, no banco do bot.
- **Calendário externo** — o Google Calendar do aluno, destino opcional do "Adicionar".

## Entidades

```
EventoCalendario
  - id
  - titulo
  - descricao
  - inicio            (datetime com timezone)
  - fim               (datetime, opcional para eventos de dia inteiro)
  - dia_inteiro       (bool)
  - audiencia         (global | curso:<X> | semestre:<N> | turma:<Y>)
  - local             (opcional)
  - criado_em
  - atualizado_em

AdicaoCalendarioExterno
  - id
  - aluno_id
  - evento_id
  - id_evento_google  (event id retornado pelo Google)
  - adicionado_em
```

## Ports

- `CalendarioRepository.proximos_eventos(audiencia_filter, horizonte) -> list[EventoCalendario]`
- `CalendarioRepository.buscar_por_id(evento_id) -> EventoCalendario`
- `CalendarioExterno.criar_evento(aluno_token, evento) -> id_externo`
- `OAuthGoogleStore.token_para(aluno_id) -> Token | None`
- `OAuthGoogleStore.salvar(aluno_id, token)`

## Adapters

- `infrastructure/persistence` — fonte interna (Postgres).
- `infrastructure/google/calendar` — cliente da API do Google Calendar (ver [[03-Integracoes/Google-Calendar]]).

## Regras

- **Fonte de verdade é o banco.** O Google Calendar não é consultado — é só destino.
- **Deduplicação**: ao criar evento no Google, marcar `extendedProperties.private.bot_evento_id = <evento_id>` para que cliques repetidos não criem duplicados (verificar antes de inserir).
- **Timezones**: armazenar e exibir em `America/Sao_Paulo` por padrão; a API do Google exige timezone IANA explícito.

## Casos de uso

- `ConsultarCalendario(aluno_id, horizonte=30d) -> list[EventoDTO]`
- `AdicionarAoGoogleCalendar(aluno_id, evento_id) -> ResultadoDTO`
- `IniciarOAuthGoogle(aluno_id) -> URL_consent`
- `ConcluirOAuthGoogle(aluno_id, code) -> ok`

→ [[01-Arquitetura/Fluxos/Fluxo-Calendario]] | [[03-Integracoes/Google-Calendar]]

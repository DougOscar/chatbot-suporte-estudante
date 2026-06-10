---
title: Integração — Google Calendar
tags: [integracao, google, oauth]
---

# Google Calendar API

## Custo

**Gratuita** dentro das quotas (1M de queries/dia por projeto, ordem de magnitude muito acima do nosso uso).

## Setup no Google Cloud Console

1. Acessar https://console.cloud.google.com → criar/usar um projeto.
2. **APIs & Services → Library** → habilitar:
   - **Google Calendar API**
   - **Google Drive API** (também usado pela [[03-Integracoes/Google-Docs-Drive|base de conhecimento]])
   - **Google Docs API**
3. **APIs & Services → OAuth consent screen**:
   - User type: **External**
   - Preencher nome do app, email de suporte, logo (opcional)
   - **Scopes** a adicionar: `https://www.googleapis.com/auth/calendar.events` (apenas eventos — não precisa de acesso total ao calendário)
   - **Test users**: enquanto o app não for publicado, adicionar os e-mails dos alunos que vão testar
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Web application** (ou Desktop, dependendo do fluxo final)
   - Authorized redirect URIs: a URL do callback do bot (ex.: `https://meu-bot.exemplo.com/oauth/google/callback`)
5. Baixar o JSON do client → salvar como o arquivo apontado por `GOOGLE_OAUTH_CLIENT_SECRETS_PATH` no `.env`. **Nunca commitar.**

## Fluxo OAuth no bot

O OAuth é **por aluno** — cada aluno autoriza individualmente para que o bot crie eventos no calendário **dele**.

1. Aluno clica "Adicionar ao Google Calendar" pela primeira vez.
2. Bot responde com link de consent: `https://accounts.google.com/o/oauth2/auth?...&state=<aluno_id>`.
3. Aluno autoriza no browser → Google redireciona para nosso callback com `code`.
4. Bot troca `code` por `access_token + refresh_token`, criptografa e salva no banco (tabela `oauth_google_token`, ligada a `aluno_id`).
5. Próximas vezes: usa `refresh_token` para renovar o `access_token` automaticamente.

Detalhe do fluxo: [[01-Arquitetura/Fluxos/Fluxo-Calendario]].

## Scope mínimo necessário

```
https://www.googleapis.com/auth/calendar.events
```

Esse scope permite **criar e gerenciar apenas os eventos que o app criou** — não vê eventos pré-existentes do aluno. É o menor escopo que atende.

## Modo de publicação

- Enquanto em desenvolvimento/testes: **Testing** com até 100 usuários de teste cadastrados manualmente.
- Para produção aberta a todos os alunos: precisa de **verificação do app** pela Google, que pode levar dias/semanas (especialmente para scopes sensíveis — `calendar.events` é não-sensível, então deve ser rápido).

## Estrutura do evento criado

```python
{
    "summary": evento.titulo,
    "description": evento.descricao,
    "start": {"dateTime": evento.inicio, "timeZone": "America/Sao_Paulo"},
    "end":   {"dateTime": evento.fim,    "timeZone": "America/Sao_Paulo"},
    "location": evento.local,
    "extendedProperties": {
        "private": {"bot_evento_id": str(evento.id)}
    },
}
```

A `extendedProperties.private.bot_evento_id` é usada para **deduplicação** — antes de criar, listamos eventos com essa propriedade para evitar duplicados.

## Referências

- Calendar API: https://developers.google.com/calendar/api
- OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Biblioteca Python sugerida: `google-auth`, `google-api-python-client`

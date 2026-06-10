---
title: Integração — Telegram (criação do bot via BotFather)
tags: [integracao, telegram, setup]
---

# Telegram — criando o bot

Pré-requisito: ter uma conta no Telegram (qualquer celular/desktop serve).

## Passo a passo

1. Abra o Telegram e busque por **`@BotFather`**. Clique no resultado verificado (estrela azul).

2. Inicie a conversa e envie `/start`. O BotFather lista os comandos disponíveis.

3. Envie `/newbot`. Ele vai pedir:
   - **Display name** do bot (ex.: `Suporte ao Estudante`).
   - **Username** do bot. Tem que terminar com `bot` (ex.: `suporte_estudante_<faculdade>_bot`). Precisa ser único no Telegram inteiro.

4. O BotFather responderá com uma mensagem contendo o **token HTTP API** no formato:
   ```
   123456789:AAH...
   ```
   **Esse é o `TELEGRAM_BOT_TOKEN`** que vai no `.env`. **Nunca commitar.**

5. (Opcional, recomendado) Configurações adicionais via BotFather:
   - `/setdescription` — descrição que aparece na tela inicial do bot
   - `/setabouttext` — texto na bio
   - `/setuserpic` — foto de perfil
   - `/setcommands` — lista de comandos slash registrados (ver lista abaixo)
   - `/setprivacy` → **Disable** se o bot precisa ler mensagens em grupos (não é nosso caso, manter habilitado para responder só a DMs ou mensagens dirigidas)

## Comandos sugeridos (para `/setcommands`)

Cole no BotFather quando ele perguntar:

```
start - Iniciar conversa com o bot
vincular - Vincular sua conta de aluno
matricula - Consultar status da matrícula
pagamento - Consultar próximo pagamento
calendario - Ver próximas datas importantes
ajuda - Lista de comandos disponíveis
```

## Modos de operação

- **Polling** — o bot pergunta ao Telegram por novas mensagens em loop. **Recomendado em desenvolvimento.** Sem necessidade de domínio público.
- **Webhook** — o Telegram envia HTTP POST para uma URL pública nossa. **Recomendado em produção.** Requer HTTPS e domínio público.

Configuração via variável `TELEGRAM_MODE` no `.env` — ver [[04-Operacoes/Variaveis-de-Ambiente]] e [[04-Operacoes/Deploy]].

## Custos

Telegram Bot API é **gratuita**, sem rate limits práticos para o volume esperado de um chatbot acadêmico.

## Referências

- BotFather: https://t.me/BotFather
- API oficial: https://core.telegram.org/bots/api
- Biblioteca usada: https://python-telegram-bot.org

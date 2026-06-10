---
title: Fluxo — Mensagem genérica (intent routing)
tags: [fluxo, sequencia, conversa]
---

# Fluxo — Mensagem genérica

Sequência canônica de uma mensagem qualquer chegando pelo Telegram.

```mermaid
sequenceDiagram
    autonumber
    actor Aluno
    participant TG as Telegram API
    participant H as Handler<br/>(interfaces)
    participant UC as Processar Mensagem<br/>(application)
    participant CONV as Conversa<br/>(domain)
    participant CTX as Use cases<br/>de contexto
    participant LLM as LLM Gateway
    participant LOG as Registrar Interação
    participant DB as Postgres

    Aluno->>TG: "quando vence minha próxima mensalidade?"
    TG->>H: update
    H->>UC: ProcessarMensagem(usuario, texto)
    UC->>CONV: classificar_intencao(texto)
    CONV-->>UC: intencao = PROXIMO_PAGAMENTO
    UC->>CTX: ConsultarProximoPagamento(usuario)
    CTX-->>UC: PagamentoDTO(valor, vencimento, link_boleto)
    UC->>LLM: gerar_resposta(intencao, contexto, persona)
    LLM-->>UC: texto + tokens_in + tokens_out
    UC->>LOG: registrar(msg, ctx, resp, tokens)
    LOG->>DB: INSERT interacao
    UC-->>H: resposta
    H->>TG: sendMessage(resposta)
    TG->>Aluno: resposta
```

## Notas

- **Intent routing** começa simples (heurísticas + few-shot na LLM) e pode evoluir para classificador dedicado se necessário. Ver [[02-Dominios/Conversa]].
- O passo `gerar_resposta` recebe o contexto **estruturado** (DTOs), não dados brutos da API externa — isso isola o prompt da forma da integração.
- O registro de interação acontece **sempre**, inclusive em caminhos de erro. Ver [[01-Arquitetura/Fluxos/Fluxo-Logging]].
- Caso a intenção exija múltiplos contextos (ex.: "me lembra do calendário e quando vence?"), o use case dispara em paralelo e agrega.

## Variações relevantes

- [[01-Arquitetura/Fluxos/Fluxo-Matricula]]
- [[01-Arquitetura/Fluxos/Fluxo-Pagamentos]]
- [[01-Arquitetura/Fluxos/Fluxo-Calendario]]
- [[01-Arquitetura/Fluxos/Fluxo-FAQ-RAG]]

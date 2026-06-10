---
title: Fluxo — Próximo pagamento
tags: [fluxo, sequencia, financeiro]
---

# Fluxo — Próximo pagamento

```mermaid
sequenceDiagram
    autonumber
    actor Aluno
    participant H as Handler
    participant UC as ConsultarProximoPagamento
    participant Repo as FinanceiroRepository
    participant SA as Sistema Acadêmico
    participant LLM
    participant LOG

    Aluno->>H: "quando vence minha mensalidade?"
    H->>UC: ConsultarProximoPagamento(usuario)
    UC->>Repo: proximo_em_aberto(aluno_id)
    Repo->>SA: GET /alunos/{id}/pagamentos?status=aberto&order=vencimento
    SA-->>Repo: [{valor, vencimento, url_boleto, ...}, ...]
    Repo-->>UC: Pagamento(valor=890.00, vencimento=2026-06-15, url_boleto)
    UC->>LLM: gerar_resposta(intent=PROXIMO_PAGAMENTO, dto)
    LLM-->>UC: "Sua próxima mensalidade vence em 15/06..."
    UC->>LOG: registrar(...)
    UC-->>H: resposta + botão inline com link do boleto
```

## Detalhes

- A resposta no Telegram aproveita **inline keyboard** para o link do boleto, em vez de embutir URL no texto livre (melhor UX).
- O **link do boleto** vem do sistema acadêmico; o bot apenas repassa. Não armazenamos PDFs.
- Se não há pagamento em aberto, a resposta deixa isso claro ("você não tem mensalidades em aberto").
- Estados financeiros relevantes na linguagem ubíqua: `EM_ABERTO`, `PAGO`, `VENCIDO`, `EM_NEGOCIACAO`.

→ [[02-Dominios/Financeiro]] | [[03-Integracoes/Sistema-Academico]]

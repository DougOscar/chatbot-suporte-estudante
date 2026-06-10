---
title: Domínio — Financeiro
tags: [dominio, bounded-context]
---

# Financeiro

Responde sobre pagamentos do aluno: próxima mensalidade, valor, vencimento e link para o boleto/arquivo.

## Linguagem ubíqua

- **Pagamento** — uma cobrança específica (mensalidade, taxa, multa).
- **Status do pagamento** — `EM_ABERTO`, `PAGO`, `VENCIDO`, `EM_NEGOCIACAO`.
- **Próximo pagamento** — o pagamento `EM_ABERTO` mais próximo do vencimento.

## Entidades

```
Pagamento
  - id
  - aluno_id
  - referencia        (ex.: "Mensalidade 06/2026")
  - valor
  - vencimento
  - status (StatusPagamento)
  - url_boleto         (apontamento para o sistema acadêmico)
  - pago_em            (nullable)
```

## Ports

- `FinanceiroRepository.proximo_em_aberto(aluno_id) -> Pagamento | None`
- `FinanceiroRepository.listar_pendentes(aluno_id) -> list[Pagamento]`
- `FinanceiroRepository.historico(aluno_id, periodo) -> list[Pagamento]`

## Adapter principal

- `infrastructure/sistema_academico` — mesmo client de [[02-Dominios/Matricula]].

## Decisões importantes

- **Não armazenamos boletos/PDFs.** Apenas a URL apontando para o sistema acadêmico. O aluno acessa o arquivo no portal autenticado.
- **Não exibimos valores no histórico de logs em texto plano** sem necessidade — considerar mascarar no `contexto_recuperado` de [[02-Dominios/Observabilidade]] se a política exigir.
- **Caching**: agressivamente curto (1-2 min) porque pagamentos mudam de status com frequência (no dia do pagamento, por exemplo).

## Casos de uso

- `ConsultarProximoPagamento(aluno_id) -> PagamentoDTO`
- `ListarPagamentosPendentes(aluno_id) -> list[PagamentoDTO]`

→ [[01-Arquitetura/Fluxos/Fluxo-Pagamentos]]

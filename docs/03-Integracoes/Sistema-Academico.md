---
title: Integração — Sistema Acadêmico da Faculdade
tags: [integracao, sistema-academico, pendencia]
---

# Sistema Acadêmico — placeholder

> **Status**: integração ainda **não especificada**. As decisões abaixo vão ser revisitadas assim que tivermos a API concreta da faculdade documentada.

## O que esperamos consumir

Endpoints (nomes hipotéticos — alinhar com a faculdade):

- `GET /alunos/{id}/matricula` → status + curso + semestre. Alimenta [[02-Dominios/Matricula]].
- `GET /alunos/{id}/pagamentos?status=...` → lista de pagamentos. Alimenta [[02-Dominios/Financeiro]].
- (Eventual) `GET /alunos/{id}/historico` → histórico acadêmico.

## Decisões pendentes (perguntas a fazer à equipe acadêmica)

1. **Autenticação**: API key estática? OAuth? JWT? mTLS?
2. **Identificação do aluno**: pelo `matricula_id`? CPF? e-mail?
3. **Disponibilidade**: SLA? Janelas de manutenção? Rate limits?
4. **Formato dos dados**:
   - Status de matrícula — quais valores possíveis exatos?
   - Status de pagamento — quais valores possíveis exatos?
   - URL do boleto requer autenticação ou é pública (com token)?
5. **Onboarding**: como o aluno prova ser dono daquele `matricula_id` no primeiro contato pelo Telegram? Token único enviado por e-mail? Outra forma? Ver discussão em [[02-Dominios/Matricula]].
6. **Webhooks**: a faculdade emite eventos quando status mudam (pagamento confirmado, matrícula trancada)? Se sim, podemos manter cache local mais agressivo.

## Adapter

`infrastructure/sistema_academico/` — cliente HTTP com:
- `httpx` (async) ou similar
- Retry com backoff exponencial em falhas transitórias
- Circuit breaker (opcional, decidir conforme observado em produção)
- Timeout agressivo (3-5s) — o aluno está esperando
- Logging de cada chamada externa nas métricas operacionais (não confundir com [[02-Dominios/Observabilidade]] que loga a **interação**, não as chamadas internas)

## Estratégia de degradação

Se o sistema acadêmico estiver fora, a resposta degrada para mensagem amigável ("não consegui consultar agora, tente em alguns minutos"), o erro é registrado, e idealmente um alerta operacional é emitido. **Não** consultar a LLM para inventar a resposta — o domínio de [[02-Dominios/Conversa]] deve respeitar o sinal de "indisponível" sem alucinar dados.

## Mock para desenvolvimento

Enquanto a API real não estiver pronta, o adapter pode ter um modo "mock" (controlado por env var) que retorna dados estáticos plausíveis — útil para desenvolver e testar a UX do bot sem depender da disponibilidade do sistema acadêmico.

---
title: Fluxo — Consulta de matrícula
tags: [fluxo, sequencia, matricula]
---

# Fluxo — Consulta de matrícula

```mermaid
sequenceDiagram
    autonumber
    actor Aluno
    participant H as Handler
    participant UC as ConsultarMatricula
    participant Repo as MatriculaRepository<br/>(port)
    participant SA as Sistema Acadêmico<br/>(adapter)
    participant LLM
    participant LOG as Log

    Aluno->>H: "qual minha situação?"
    H->>UC: ConsultarMatricula(usuario_telegram)
    UC->>Repo: buscar_por_aluno(id)
    Repo->>SA: GET /alunos/{id}/matricula
    SA-->>Repo: {status, curso, semestre, ...}
    Repo-->>UC: Matricula(status=ATIVA, ...)
    UC->>LLM: gerar_resposta(intent=MATRICULA, dto)
    LLM-->>UC: "Você está matriculado(a) no 5º semestre de ..."
    UC->>LOG: registrar(...)
    UC-->>H: resposta
```

## Pontos de atenção

- O aluno é identificado pelo `telegram_user_id`. O mapeamento `telegram_user_id → matricula_id` deve estar no banco (tabela `aluno`); o primeiro contato exige um onboarding/autenticação. Ver [[02-Dominios/Matricula]] para o fluxo de vínculo.
- Possíveis status (linguagem ubíqua): `ATIVA`, `TRANCADA`, `CANCELADA`, `FORMADO`, `INADIMPLENTE`. Ver [[05-Modelagem/Glossario-Ubiquo]].
- Em caso de falha do sistema acadêmico, a resposta deve degradar graciosamente ("não consegui consultar agora, tente em alguns minutos") e o erro entra no log.

→ Ver também [[03-Integracoes/Sistema-Academico]]

---
title: Domínio — Matrícula
tags: [dominio, bounded-context]
---

# Matrícula

Responsável por tudo relacionado à situação acadêmica formal do aluno: status, curso, semestre.

## Linguagem ubíqua

- **Aluno** — pessoa física com vínculo institucional ativo ou histórico.
- **Matrícula** — vínculo do aluno com um curso, num determinado período.
- **Status de matrícula** — `ATIVA`, `TRANCADA`, `CANCELADA`, `FORMADO`, `INADIMPLENTE`.

Ver também [[05-Modelagem/Glossario-Ubiquo]].

## Entidades principais

```
Aluno
  - id
  - telegram_user_id  (vínculo bot ↔ aluno)
  - nome
  - email
  - matricula_id      (chave no sistema acadêmico)
  - criado_em

Matricula
  - id
  - aluno_id
  - curso
  - semestre_atual
  - status (StatusMatricula)
  - desde
  - ultima_consulta_em  (cache local opcional)
```

## Ports (a definir no `domain/matricula`)

- `MatriculaRepository.buscar_por_aluno(aluno_id) -> Matricula`
- `AlunoRepository.vincular_telegram(telegram_user_id, dados_identificacao) -> Aluno`

## Adapter principal

- `infrastructure/sistema_academico` — HTTP client para a API da faculdade (ver [[03-Integracoes/Sistema-Academico]]).

## Vínculo Telegram ↔ Aluno (onboarding)

Pendência de produto importante: como o bot identifica o aluno na primeira interação? Opções:

1. **Comando `/vincular <matricula> <token>`** com token enviado por e-mail/SMS pelo sistema acadêmico.
2. **Deep link** do tipo `t.me/<bot>?start=<token>` gerado no portal do aluno.
3. **Login OAuth** se o sistema acadêmico expuser.

Decisão arquitetural pendente — registrar como ADR quando definida.

## Caching

A matrícula varia pouco (raramente muda durante o semestre). Considerar TTL curto (5-15 min) para reduzir chamadas ao sistema acadêmico, com **invalidação manual** via comando admin.

## Casos de uso (`application/matricula`)

- `ConsultarMatricula(aluno_id) -> MatriculaDTO`
- `VincularContaTelegram(telegram_user_id, dados) -> Aluno`

→ [[01-Arquitetura/Fluxos/Fluxo-Matricula]]

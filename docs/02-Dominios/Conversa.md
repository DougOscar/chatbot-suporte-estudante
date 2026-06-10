---
title: Domínio — Conversa
tags: [dominio, bounded-context, llm]
---

# Conversa

O orquestrador conversacional. Recebe a mensagem do aluno, descobre a intenção, dispara os outros bounded contexts para obter contexto, e chama a LLM para gerar a resposta final em pt-BR.

## Responsabilidades

- **Intent routing** — descobrir o que o aluno quer.
- **Orquestração** — disparar os casos de uso pertinentes em paralelo quando possível.
- **Prompt engineering** — montar o prompt da LLM com persona, contexto e instruções.
- **Pós-processamento** — sanitização da resposta (cortar tamanho, validar formato, remover alucinações óbvias).

## Linguagem ubíqua

- **Intenção** — categoria do que o aluno está pedindo: `MATRICULA`, `PROXIMO_PAGAMENTO`, `PAGAMENTOS_LISTAR`, `CALENDARIO`, `ADD_GCAL`, `FAQ`, `SAUDACAO`, `INDEFINIDO`.
- **Persona** — instruções fixas que definem o tom do bot (curto, conversacional, em pt-BR, sem chavões corporativos).

## Estratégia de intent routing

Etapa de detecção da intenção. Duas opções iniciais:

### Opção A — Heurísticas + LLM como fallback

1. Regras simples (keywords, regex) cobrem 70% dos casos com latência baixa.
2. Casos não classificados vão para a LLM com prompt few-shot.

**Prós**: barato, rápido. **Contras**: regras decaem com o tempo.

### Opção B — Apenas LLM (function calling / structured output)

Toda mensagem vai para a LLM que retorna a intenção em JSON estruturado. Para Gemini, OpenAI e Anthropic todos suportam structured output.

**Prós**: maior precisão em queries ambíguas, código mais limpo. **Contras**: custo por mensagem maior.

**Recomendação inicial**: começar com **Opção A** (heurísticas + fallback LLM), migrar para **B** se precisão for problema. Decisão revisitável conforme métricas.

## Construção do prompt

Estrutura recomendada:

```
[SISTEMA]
Você é o assistente virtual da <Faculdade>. Responda em pt-BR de forma curta,
clara e amigável (máximo ~3 frases). Use apenas as informações em [CONTEXTO].
Se a informação não estiver no contexto, diga que não sabe e sugira o canal correto.
Nunca invente datas, valores ou status.

[CONTEXTO]
{json_estruturado_do_caso_de_uso}

[USUARIO]
{texto_do_aluno}
```

## Persona

Definir tom único e versionar como constante (`PROMPT_VERSAO=1`). Mudanças de persona devem ser registradas nos logs de [[02-Dominios/Observabilidade]] (campo `prompt_versao`).

## Casos de uso

- `ProcessarMensagem(usuario, texto) -> RespostaDTO` ← orquestrador principal
- `ClassificarIntencao(texto) -> Intencao`
- `GerarResposta(intencao, contexto, persona) -> RespostaTexto + tokens`

## Ports

- `LLMGateway.gerar(prompt, max_tokens) -> RespostaLLM(texto, tokens_in, tokens_out)`
- `LLMGateway.classificar_intencao(texto) -> Intencao + tokens` (opcional, Opção B)

## Sobre histórico de conversa

Decisão inicial: **stateless** — cada mensagem é processada isoladamente. Manter sessão de N turnos requer trade-offs de custo (tokens) e privacidade. Pode ser adicionado depois com tabela `sessao_conversa` ligando turnos.

→ [[01-Arquitetura/Fluxos/Fluxo-Mensagem-Generico]] | [[03-Integracoes/LLM-Provedores]]

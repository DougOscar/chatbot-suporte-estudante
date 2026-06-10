---
title: Integração — Provedores de LLM
tags: [integracao, llm]
---

# Provedores de LLM

A camada `LLMGateway` (port do domínio de [[02-Dominios/Conversa]]) abstrai o provedor. Os adapters concretos vivem em `infrastructure/llm/`.

## Comparativo

| Provedor | Modelo sugerido | Free tier? | Custo aprox. (in / out por 1M tokens) | Qualidade pt-BR | Latência |
|---|---|---|---|---|---|
| **Google Gemini** | `gemini-2.5-flash` | **Sim** — quota generosa | $0.30 / $2.50 | Muito boa | Baixa |
| **Anthropic Claude** | `claude-haiku-4-5` | Não (créditos iniciais) | $1.00 / $5.00 | Excelente | Baixa |
| **OpenAI** | `gpt-4o-mini` | Não (créditos iniciais) | $0.15 / $0.60 | Muito boa | Baixa |
| **Groq** | `llama-3.3-70b-versatile` | **Sim** — quota generosa | $0.59 / $0.79 (após free) | Boa | **Muito baixa** |
| **Ollama (local)** | `llama3.2` / `qwen2.5` | **Sim** (zero custo) | $0 (custo de hardware) | Razoável (depende do modelo) | Depende da máquina |

> Preços são referência para validação do projeto e mudam sem aviso — verificar nas páginas oficiais antes de orçar.

## Recomendação

- **Desenvolvimento e validação**: **Gemini Flash** (free tier robusto, suporta structured output, embeddings inclusos no mesmo provedor).
- **Produção com orçamento**: **Claude Haiku** ou **GPT-4o-mini** — qualidade conversacional notavelmente melhor em respostas curtas em pt-BR.
- **Produção com restrição de custo zero**: **Gemini Flash** (mantendo free tier) ou self-hosted via Ollama em VM com GPU/Apple Silicon.

## Estratégia de "swap de provedor"

`LLMGateway` é um Protocol em `domain/conversa`:

```
class LLMGateway(Protocol):
    async def gerar(self, prompt: Prompt, max_tokens: int) -> RespostaLLM: ...
    async def embed(self, texto: str) -> Vetor: ...   # ou em gateway separado
```

Cada adapter (`infrastructure/llm/gemini.py`, `.../anthropic.py`, etc.) normaliza:
- Formato do prompt (system / user)
- Resposta (texto + `tokens_entrada` + `tokens_saida`)
- Erros (rate limit, indisponível) em exceções de domínio comuns

A escolha do adapter concreto vem da variável `LLM_PROVIDER` no [[04-Operacoes/Variaveis-de-Ambiente|.env]].

## Structured output (para intent routing)

Todos os provedores listados suportam JSON estruturado:
- **Gemini**: `response_mime_type="application/json"` + `response_schema`
- **Anthropic**: tool use com schema
- **OpenAI**: `response_format={"type": "json_schema", ...}`
- **Groq**: compatível com formato OpenAI

Isso vai ser útil quando/se migrarmos para Opção B do intent routing (ver [[02-Dominios/Conversa]]).

## Embeddings

Discussão equivalente, mas separada — algumas opções:
- **Gemini**: `text-embedding-004` (dim 768) — free tier
- **OpenAI**: `text-embedding-3-small` (dim 1536) — barato
- **sentence-transformers local**: `intfloat/multilingual-e5-base` (dim 768) — gratuito, roda em CPU para volumes baixos

Decisão padrão: **Gemini embeddings** enquanto o provedor de LLM também for Gemini (consolida em uma única chave de API).

## Sobre alucinação

Independente do provedor, o **prompt de sistema** (ver [[02-Dominios/Conversa]]) deve enfatizar:
- Responder apenas com informações do `[CONTEXTO]`
- Quando não souber, dizer que não sabe e indicar canal alternativo
- Nunca inventar valores monetários, datas, status

Isso é especialmente crítico para [[02-Dominios/Financeiro]] e [[02-Dominios/Matricula]].

## Referências

- Gemini: https://ai.google.dev/
- Anthropic: https://docs.anthropic.com
- OpenAI: https://platform.openai.com/docs
- Groq: https://console.groq.com/docs
- Ollama: https://ollama.com

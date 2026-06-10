---
title: Integração — Google Docs + Drive (base de conhecimento)
tags: [integracao, google, kb, rag]
---

# Google Docs + Drive — base de conhecimento

## Custo

**Gratuita** dentro das quotas (Docs API: 60 reqs/min/usuário; Drive API: 1.000 reqs/100s/usuário). Suficiente para sincronização periódica.

## Modelo de acesso: Service Account (recomendado)

Diferente do [[03-Integracoes/Google-Calendar|Calendar]] (que é por aluno), a base de conhecimento é institucional. Usamos uma **service account** dedicada:

1. No mesmo projeto Google Cloud usado para Calendar → **APIs habilitadas**: Drive + Docs.
2. **IAM & Admin → Service Accounts → Create Service Account**:
   - Nome: `kb-sync` (ou similar)
   - Roles: nenhum a nível de projeto Google (acesso é via compartilhamento dos docs)
3. Criar uma **chave JSON** para a service account → baixar e salvar como o arquivo apontado por `GOOGLE_OAUTH_CLIENT_SECRETS_PATH` (ou um path dedicado). **Nunca commitar.**
4. **Compartilhar a pasta da KB com o e-mail da service account** (permissão "Viewer" basta):
   - No Drive, abrir a pasta que conterá os docs da base de conhecimento
   - Botão "Compartilhar" → adicionar `kb-sync@<projeto>.iam.gserviceaccount.com` como Viewer
5. Copiar o **ID da pasta** (parte final da URL `drive.google.com/drive/folders/<ID>`) para a variável `GOOGLE_DRIVE_KB_FOLDER_ID`.

## Por que service account em vez de OAuth?

- Sincronização é offline (cron job) — não há usuário interativo.
- Acesso é controlado **explicitamente** via compartilhamento da pasta.
- Não há refresh token expirando.

## Fluxo de sincronização

Detalhado em [[01-Arquitetura/Fluxos/Fluxo-FAQ-RAG]] (seção "Ingestão").

Resumo:
1. `Drive.files.list(q="'<folder_id>' in parents and mimeType='application/vnd.google-apps.document'")` → lista de doc IDs + `modifiedTime`.
2. Comparar `modifiedTime` com o `atualizado_em_origem` registrado.
3. Para docs novos/modificados: `Docs.documents.get(<docId>)` → extrair texto.
4. Chunk → embed → upsert no banco (pgvector).
5. Para docs removidos da pasta: limpar chunks órfãos.

## Scopes necessários

```
https://www.googleapis.com/auth/drive.readonly
https://www.googleapis.com/auth/documents.readonly
```

Apenas leitura. O bot **nunca escreve** nos docs.

## Estrutura sugerida da pasta KB no Drive

```
KB-Suporte-Estudante/
├── FAQs/
│   ├── FAQ Matrícula.gdoc
│   ├── FAQ Pagamentos.gdoc
│   └── FAQ Calendário.gdoc
└── Políticas Internas/
    ├── Política de Trancamento.gdoc
    ├── Política de Reembolso.gdoc
    └── Regulamento Acadêmico.gdoc
```

A listagem é recursiva (subpastas opcional — definir na implementação se vamos descer ou não).

## Extração de texto

A Docs API retorna estrutura rica (headers, listas, tabelas). Para o RAG queremos:
- Preservar headers (servem como contexto e como pontos de chunking)
- Achatar listas em texto simples
- Tabelas → markdown ou texto simples linha-a-linha

Decisão de detalhe a tomar na implementação. Ver [[02-Dominios/Conhecimento]] para estratégias de chunking.

## Referências

- Drive API: https://developers.google.com/drive/api/reference/rest/v3
- Docs API: https://developers.google.com/docs/api
- Service Accounts: https://cloud.google.com/iam/docs/service-account-overview

"""Caso de uso ``SincronizarKB``.

MVP: full re-sync sempre (idempotente via UPSERT do documento e
substituição completa dos chunks). Não detecta documentos removidos da
fonte por enquanto — adicionar quando precisar.

Fluxo:
    listar docs da fonte → para cada doc → carrega texto → chunk →
    embed batch → upsert(doc) + substituir_chunks(doc, chunks)
"""

import hashlib

import structlog

from chatbot.domain.conhecimento import (
    ChunkKB,
    EmbeddingGateway,
    KbRepository,
    KbSyncSource,
    ResumoSincronizacao,
    chunk_texto,
)

_log = structlog.get_logger(__name__)


class SincronizarKB:
    def __init__(
        self,
        *,
        source: KbSyncSource,
        repository: KbRepository,
        embeddings: EmbeddingGateway,
        max_chars_por_chunk: int = 2400,
    ) -> None:
        self._source = source
        self._repository = repository
        self._embeddings = embeddings
        self._max_chars = max_chars_por_chunk

    async def __call__(self) -> ResumoSincronizacao:
        resumo = ResumoSincronizacao()
        documentos = await self._source.listar_documentos()

        for documento in documentos:
            try:
                texto = await self._source.carregar_texto(documento.id)
            except Exception as exc:
                resumo.erros.append(f"{documento.id}: carregar_texto: {exc}")
                _log.warning(
                    "kb_sync_falha_carregar",
                    documento_id=documento.id,
                    error=str(exc),
                )
                continue

            hash_novo = hashlib.sha256(texto.encode("utf-8")).hexdigest()
            chunks_texto = chunk_texto(texto, max_chars=self._max_chars)

            if not chunks_texto:
                resumo.documentos_pulados += 1
                continue

            try:
                vetores = await self._embeddings.embed_batch(chunks_texto)
            except Exception as exc:
                resumo.erros.append(f"{documento.id}: embed_batch: {exc}")
                _log.warning(
                    "kb_sync_falha_embeddings",
                    documento_id=documento.id,
                    error=str(exc),
                )
                continue

            chunks_dominio = [
                ChunkKB(
                    documento_id=documento.id,
                    indice=i,
                    texto=t,
                    embedding=v,
                )
                for i, (t, v) in enumerate(zip(chunks_texto, vetores, strict=True))
            ]

            # Substitui hash_conteudo no doc antes de persistir.
            documento_com_hash = documento.__class__(
                id=documento.id,
                titulo=documento.titulo,
                url=documento.url,
                atualizado_em_origem=documento.atualizado_em_origem,
                hash_conteudo=hash_novo,
            )

            try:
                await self._repository.upsert_documento(documento_com_hash)
                await self._repository.substituir_chunks(documento.id, chunks_dominio)
            except Exception as exc:
                resumo.erros.append(f"{documento.id}: persistir: {exc}")
                _log.warning(
                    "kb_sync_falha_persistir",
                    documento_id=documento.id,
                    error=str(exc),
                )
                continue

            resumo.documentos_processados += 1
            resumo.chunks_inseridos += len(chunks_dominio)

        return resumo

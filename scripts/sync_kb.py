"""Sincroniza a base de conhecimento (Google Docs → pgvector).

Em dev (sem ``GOOGLE_DRIVE_KB_FOLDER_ID``) usa ``MockKbSource`` com
4 documentos hardcoded. Quando o adapter real (service account Drive +
Docs API) for implementado, troca-se aqui.

Rodar::

    uv run python scripts/sync_kb.py
"""

import asyncio

from chatbot.application.conhecimento import SincronizarKB
from chatbot.config import DatabaseSettings, EmbeddingSettings, GoogleSettings
from chatbot.domain.conhecimento import EmbeddingGateway, KbSyncSource
from chatbot.infrastructure.google.docs.mock_kb_source import MockKbSource
from chatbot.infrastructure.llm.null_embeddings import NullEmbeddingsGateway
from chatbot.infrastructure.persistence.engine import create_engine, create_session_factory
from chatbot.infrastructure.persistence.kb_repository import SqlAlchemyKbRepository


def _construir_source(google: GoogleSettings) -> KbSyncSource:
    if not google.drive_kb_folder_id:
        return MockKbSource()
    raise NotImplementedError(
        "Adapter Google Drive+Docs ainda não implementado. Deixe "
        "GOOGLE_DRIVE_KB_FOLDER_ID vazio para usar o mock."
    )


def _construir_embeddings(embed: EmbeddingSettings) -> EmbeddingGateway:
    if embed.api_key is None or not embed.api_key.get_secret_value():
        return NullEmbeddingsGateway()
    if embed.provider == "gemini":
        from chatbot.infrastructure.llm.gemini_embeddings import GeminiEmbeddingsGateway

        return GeminiEmbeddingsGateway(
            api_key=embed.api_key.get_secret_value(),
            model=embed.model,
        )
    raise NotImplementedError(
        f"Provedor de embeddings '{embed.provider}' não implementado. Suportados: gemini."
    )


async def _executar() -> None:
    engine = create_engine(DatabaseSettings().url)
    factory = create_session_factory(engine)
    try:
        source = _construir_source(GoogleSettings())
        embeddings = _construir_embeddings(EmbeddingSettings())
        repository = SqlAlchemyKbRepository(factory)
        sincronizar = SincronizarKB(source=source, repository=repository, embeddings=embeddings)

        resumo = await sincronizar()
        print(
            f"Sincronização concluída.\n"
            f"  Documentos processados: {resumo.documentos_processados}\n"
            f"  Documentos pulados (vazios): {resumo.documentos_pulados}\n"
            f"  Chunks inseridos: {resumo.chunks_inseridos}\n"
            f"  Erros: {len(resumo.erros)}"
        )
        for erro in resumo.erros:
            print(f"    - {erro}")
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(_executar())


if __name__ == "__main__":
    main()

"""Smoke tests da camada de persistência.

Verifica que os modelos estão registrados na metadata e que estruturas
relevantes (chaves, índices, FKs) batem com o desenho do schema.
"""

from chatbot.infrastructure.persistence import models  # noqa: F401  (registra)
from chatbot.infrastructure.persistence.base import Base


class TestMetadata:
    def test_todas_as_tabelas_registradas(self) -> None:
        esperadas = {
            "aluno",
            "matricula_cache",
            "oauth_google_token",
            "evento_calendario",
            "adicao_calendario_externo",
            "documento_kb",
            "kb_chunk",
            "interacao",
        }

        registradas = set(Base.metadata.tables.keys())

        assert esperadas == registradas

    def test_aluno_tem_unique_em_telegram_user_id(self) -> None:
        tabela = Base.metadata.tables["aluno"]
        col = tabela.columns["telegram_user_id"]

        assert col.unique is True

    def test_interacao_aluno_id_e_nullable_com_set_null(self) -> None:
        tabela = Base.metadata.tables["interacao"]
        col = tabela.columns["aluno_id"]
        fks = list(col.foreign_keys)

        assert col.nullable is True
        assert len(fks) == 1
        assert fks[0].ondelete == "SET NULL"

    def test_dependentes_de_aluno_tem_cascade(self) -> None:
        for nome in ("matricula_cache", "oauth_google_token", "adicao_calendario_externo"):
            tabela = Base.metadata.tables[nome]
            fks = list(tabela.columns["aluno_id"].foreign_keys)

            assert len(fks) == 1, nome
            assert fks[0].ondelete == "CASCADE", nome

    def test_kb_chunk_referencia_documento_kb(self) -> None:
        tabela = Base.metadata.tables["kb_chunk"]
        fks = list(tabela.columns["documento_id"].foreign_keys)

        assert len(fks) == 1
        assert fks[0].column.table.name == "documento_kb"


class TestModuloEngine:
    def test_imports_carregam_sem_database_url(self) -> None:
        # O módulo `engine` não pode rodar `get_settings()` no import —
        # callers devem poder importá-lo sem `DATABASE_URL` configurado.
        from chatbot.infrastructure.persistence import engine

        assert callable(engine.create_engine)
        assert callable(engine.create_session_factory)

"""Smoke dos repositórios mock do sistema acadêmico."""

from datetime import date
from decimal import Decimal

from chatbot.domain.financeiro import StatusPagamento
from chatbot.domain.matricula import StatusMatricula
from chatbot.infrastructure.sistema_academico.mock_financeiro_repository import (
    MockFinanceiroRepository,
)
from chatbot.infrastructure.sistema_academico.mock_matricula_repository import (
    MockMatriculaRepository,
)


class TestMockMatriculaRepository:
    async def test_retorna_aluno_ativo(self) -> None:
        repo = MockMatriculaRepository()

        m = await repo.buscar_por_telegram(telegram_user_id=12345)

        assert m is not None
        assert m.status == StatusMatricula.ATIVA
        assert m.curso == "Análise e Desenvolvimento de Sistemas"
        assert m.semestre_atual == 5
        assert m.nome_aluno == "Aluno Teste"
        assert m.desde == date(2022, 2, 15)

    async def test_mesmo_dado_para_qualquer_telegram_id(self) -> None:
        # Documenta limitação do MVP: sem onboarding, o mock ignora o id.
        repo = MockMatriculaRepository()

        m1 = await repo.buscar_por_telegram(telegram_user_id=1)
        m2 = await repo.buscar_por_telegram(telegram_user_id=999)

        assert m1 == m2


class TestMockFinanceiroRepository:
    async def test_proximo_em_aberto_tem_valor_em_decimal(self) -> None:
        repo = MockFinanceiroRepository()

        p = await repo.proximo_em_aberto(telegram_user_id=12345)

        assert p is not None
        assert isinstance(p.valor, Decimal)
        assert p.status == StatusPagamento.EM_ABERTO
        assert p.url_boleto is not None and p.url_boleto.startswith("https://")

    async def test_listar_pendentes_inclui_proximo(self) -> None:
        repo = MockFinanceiroRepository()

        pendentes = await repo.listar_pendentes(telegram_user_id=12345)

        assert len(pendentes) >= 1
        assert all(p.status == StatusPagamento.EM_ABERTO for p in pendentes)

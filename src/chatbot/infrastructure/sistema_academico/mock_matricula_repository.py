"""Repositório fake de Matrícula para desenvolvimento sem API real.

Retorna sempre o mesmo aluno fictício, **independente** do ``telegram_user_id``
— suficiente para exercitar a UI conversacional enquanto onboarding e
integração com a API da faculdade não existem.
"""

from datetime import date

from chatbot.domain.matricula import Matricula, StatusMatricula


class MockMatriculaRepository:
    """Implementa ``MatriculaRepository`` por duck-typing."""

    _MOCK = Matricula(
        matricula_id_externo="2024001234",
        status=StatusMatricula.ATIVA,
        curso="Análise e Desenvolvimento de Sistemas",
        semestre_atual=5,
        nome_aluno="Aluno Teste",
        desde=date(2022, 2, 15),
    )

    async def buscar_por_telegram(self, telegram_user_id: int) -> Matricula | None:
        return self._MOCK

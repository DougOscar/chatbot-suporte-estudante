"""Testes dos value objects do domínio de Conversa."""

import pytest

from chatbot.domain.conversa import PERSONA_PADRAO, Intencao, RespostaLLM


class TestIntencao:
    def test_valores_serializam_como_string(self) -> None:
        assert Intencao.CALENDARIO == "CALENDARIO"
        assert Intencao.CALENDARIO.value == "CALENDARIO"

    def test_comparavel_a_string_pura(self) -> None:
        # StrEnum garante igualdade com a string crua — útil para queries no banco.
        assert Intencao.SAUDACAO == "SAUDACAO"
        assert Intencao.INDEFINIDO == "INDEFINIDO"

    def test_inclui_todas_as_intencoes_do_glossario(self) -> None:
        esperadas = {
            "SAUDACAO",
            "CALENDARIO",
            "ADD_GCAL",
            "MATRICULA",
            "PROXIMO_PAGAMENTO",
            "PAGAMENTOS_LISTAR",
            "FAQ",
            "INDEFINIDO",
        }
        assert {i.value for i in Intencao} == esperadas


class TestPersona:
    def test_persona_padrao_versionada(self) -> None:
        assert PERSONA_PADRAO.versao == "mvp-llm-1"
        assert len(PERSONA_PADRAO.instrucoes_sistema) > 0

    def test_persona_imutavel(self) -> None:
        with pytest.raises(Exception):
            PERSONA_PADRAO.versao = "outra"  # type: ignore[misc]

    def test_persona_padrao_contem_diretrizes_chave(self) -> None:
        instr = PERSONA_PADRAO.instrucoes_sistema
        assert "português do Brasil" in instr
        assert "CONTEXTO" in instr
        assert "NUNCA invente" in instr


class TestRespostaLLM:
    def test_construcao(self) -> None:
        r = RespostaLLM(
            texto="oi",
            tokens_entrada=10,
            tokens_saida=5,
            modelo="gemini-2.5-flash",
            provider="gemini",
        )
        assert r.texto == "oi"
        assert r.tokens_entrada == 10
        assert r.tokens_saida == 5

    def test_imutavel(self) -> None:
        r = RespostaLLM(
            texto="x",
            tokens_entrada=0,
            tokens_saida=0,
            modelo="m",
            provider="p",
        )
        with pytest.raises(Exception):
            r.texto = "y"  # type: ignore[misc]

"""Testes da função pura ``chunk_texto``."""

import pytest

from chatbot.domain.conhecimento import chunk_texto


def test_texto_vazio_retorna_lista_vazia() -> None:
    assert chunk_texto("") == []
    assert chunk_texto("   \n  ") == []


def test_texto_curto_vira_um_chunk_unico() -> None:
    texto = "Apenas um parágrafo curto."
    chunks = chunk_texto(texto, max_chars=100)
    assert chunks == [texto]


def test_paragrafos_juntam_ate_limite() -> None:
    p1 = "x" * 50
    p2 = "y" * 50
    p3 = "z" * 50
    texto = f"{p1}\n\n{p2}\n\n{p3}"
    chunks = chunk_texto(texto, max_chars=120)
    # p1+p2 (50+2+50=102) cabem juntos; p3 abre novo chunk.
    assert len(chunks) == 2
    assert p1 in chunks[0] and p2 in chunks[0]
    assert chunks[1] == p3


def test_paragrafo_gigante_isolado_passa_inteiro() -> None:
    # Preserva limite semântico ainda que ultrapasse max_chars.
    p_grande = "x" * 5000
    chunks = chunk_texto(p_grande, max_chars=2400)
    assert chunks == [p_grande]


def test_preserva_quebra_de_paragrafo_no_chunk() -> None:
    texto = "primeiro parágrafo.\n\nsegundo parágrafo."
    chunks = chunk_texto(texto, max_chars=200)
    assert chunks == ["primeiro parágrafo.\n\nsegundo parágrafo."]


@pytest.mark.parametrize("max_chars", [100, 500, 2400])
def test_chunks_individualmente_dentro_do_limite_quando_paragrafos_cabem(
    max_chars: int,
) -> None:
    # Constrói parágrafos cada um menor que max_chars.
    paragrafos = ["a" * (max_chars // 4) for _ in range(10)]
    texto = "\n\n".join(paragrafos)
    chunks = chunk_texto(texto, max_chars=max_chars)
    for c in chunks:
        assert len(c) <= max_chars


def test_lines_em_branco_consecutivas_nao_geram_chunks_vazios() -> None:
    texto = "a\n\n\n\nb\n\n\n\n\nc"
    chunks = chunk_texto(texto, max_chars=1000)
    # Tudo em um chunk só (cabe), mas o ponto é: sem chunks vazios.
    assert all(c.strip() for c in chunks)

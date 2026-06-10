"""Source fake da base de conhecimento — para dev sem service account Google.

Devolve 4 documentos institucionais hardcoded cobrindo temas frequentes:
trancamento, reembolso, biblioteca e estágio. Suficiente para exercitar
o pipeline de RAG ponta-a-ponta.
"""

from datetime import UTC, datetime

from chatbot.domain.conhecimento import DocumentoKB

_DOCS: dict[str, tuple[str, str, str]] = {
    "mock-doc-trancamento": (
        "Política de Trancamento de Matrícula",
        "https://docs.exemplo.edu.br/politica-trancamento",
        """\
A solicitação de trancamento de matrícula deve ser feita pelo portal do aluno
até o último dia útil da quarta semana do semestre letivo.

O trancamento é permitido por até quatro semestres consecutivos. Após esse
período, o aluno precisa solicitar reativação por meio da coordenação do curso,
sujeita à aprovação do colegiado.

Durante o trancamento o aluno não paga mensalidade nem mantém acesso a
plataformas restritas (Moodle, laboratórios). O e-mail institucional permanece
ativo. A condição de "TRANCADA" aparece como status de matrícula no sistema
acadêmico.

Para reativar após o trancamento, é necessário regularizar pendências
financeiras (se houver) e estar dentro do prazo de reabertura.
""",
    ),
    "mock-doc-reembolso": (
        "Política de Reembolso de Mensalidade",
        "https://docs.exemplo.edu.br/politica-reembolso",
        """\
O aluno tem direito ao reembolso integral da mensalidade se solicitar o
cancelamento da matrícula em até 7 dias corridos a partir do pagamento — desde
que não tenha frequentado nenhuma aula.

Após 7 dias e antes do início do semestre letivo, o reembolso é parcial: 80%
do valor pago. Iniciado o semestre, não há mais reembolso, apenas trancamento.

A solicitação é feita pelo portal financeiro do aluno. O valor é creditado em
até 30 dias úteis na mesma forma de pagamento utilizada originalmente.

Em caso de erro de cobrança (duplicidade, mensalidade cobrada após cancelamento),
o reembolso é imediato e não está sujeito a esses prazos.
""",
    ),
    "mock-doc-biblioteca": (
        "Regulamento da Biblioteca Central",
        "https://docs.exemplo.edu.br/biblioteca",
        """\
Cada aluno pode emprestar até 5 livros simultaneamente, por um prazo de 14
dias corridos. A renovação pode ser feita pelo portal, no máximo duas vezes
consecutivas, se não houver reserva pendente.

O atraso na devolução gera multa de R$ 2,00 por livro por dia útil, com teto
de R$ 50,00 por título. Enquanto houver multa em aberto, novos empréstimos
ficam bloqueados.

Horário de funcionamento: segunda a sexta, 8h às 22h; sábados, 9h às 13h.
Em períodos de avaliação a biblioteca estende para domingo, 14h às 20h.

Livros marcados como "reserva técnica" são de uso somente no local — não saem
do prédio da biblioteca.
""",
    ),
    "mock-doc-estagio": (
        "Procedimento para Convalidação de Estágio Curricular",
        "https://docs.exemplo.edu.br/estagio",
        """\
O estágio curricular é obrigatório a partir do 5º semestre e tem carga horária
mínima de 200 horas para integralização.

Antes de iniciar o estágio, o aluno precisa: (1) ter um plano de atividades
assinado pelo supervisor da empresa, (2) ter o termo de compromisso assinado
pela coordenação de estágios da faculdade, (3) estar matriculado regularmente
no semestre.

A apresentação do relatório final e do parecer do supervisor é feita ao
término do período, com prazo de até 30 dias após a última semana de estágio.

Estágios não-obrigatórios também podem ser feitos a partir do 3º semestre,
desde que o aluno mantenha frequência mínima nas disciplinas regulares.
""",
    ),
}

_ATUALIZADO_EM = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)


class MockKbSource:
    """Implementa ``KbSyncSource`` por duck-typing."""

    async def listar_documentos(self) -> list[DocumentoKB]:
        return [
            DocumentoKB(
                id=doc_id,
                titulo=titulo,
                url=url,
                atualizado_em_origem=_ATUALIZADO_EM,
            )
            for doc_id, (titulo, url, _) in _DOCS.items()
        ]

    async def carregar_texto(self, documento_id: str) -> str:
        if documento_id not in _DOCS:
            raise KeyError(f"documento desconhecido no mock: {documento_id!r}")
        return _DOCS[documento_id][2]

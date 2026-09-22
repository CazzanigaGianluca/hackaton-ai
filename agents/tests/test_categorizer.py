from datetime import date

from agents.categorizer import (
    CategorizerAgent,
    categorize_transactions,
    classify_by_keyword,
)
from app.backend.models import Transaction, TransactionType


def _txn(description: str, amount: float = -10.0) -> Transaction:
    return Transaction(
        date=date(2025, 1, 15),
        description=description,
        amount=amount,
        type=TransactionType.ENTRATA if amount >= 0 else TransactionType.USCITA,
    )


def test_classify_by_keyword_matches_known_merchant():
    assert classify_by_keyword("CONAD SUPERMERCATI") == "Alimentari"


def test_classify_by_keyword_is_case_insensitive():
    assert classify_by_keyword("conad supermercati") == "Alimentari"


def test_classify_by_keyword_matches_subscription_services():
    assert classify_by_keyword("NETFLIX ABBONAMENTO") == "Intrattenimento"


def test_classify_by_keyword_returns_none_when_no_match():
    assert classify_by_keyword("QUALCOSA DI SCONOSCIUTO XYZ") is None


def test_categorize_transactions_assigns_stipendio_to_unmatched_income():
    transactions = [_txn("BONIFICO SCONOSCIUTO DA AZIENDA", amount=1500.0)]
    result = categorize_transactions(transactions)
    assert result[0].category == "Stipendio/Entrate"


def test_categorize_transactions_falls_back_to_altro_for_unmatched_expense():
    transactions = [_txn("SPESA MISTERIOSA XYZ123", amount=-42.0)]
    result = categorize_transactions(transactions)
    assert result[0].category == "Altro"


def test_categorize_transactions_preserves_order_and_count():
    transactions = [_txn("CONAD SUPERMERCATI"), _txn("NETFLIX ABBONAMENTO")]
    result = categorize_transactions(transactions)
    assert len(result) == 2
    assert result[0].category == "Alimentari"
    assert result[1].category == "Intrattenimento"


def test_classify_by_keyword_never_assigns_stipendio_to_an_expense():
    # "RIMBORSO" e' una keyword di Stipendio/Entrate, ma qui la transazione e' una
    # Uscita (pagamento), non un accredito: non deve mai finire nella categoria entrate.
    assert (
        classify_by_keyword("RIMBORSO ASSICURAZIONE AUTO", TransactionType.USCITA)
        != "Stipendio/Entrate"
    )


def test_categorize_transactions_does_not_put_an_expense_in_stipendio_entrate():
    transactions = [_txn("RIMBORSO ASSICURAZIONE AUTO", amount=-45.0)]
    result = categorize_transactions(transactions)
    assert result[0].category != "Stipendio/Entrate"


async def test_categorizer_agent_applies_fallback_when_llm_returns_fewer_categories():
    class _ShortResponseLLMClient:
        class messages:
            @staticmethod
            async def create(**kwargs):
                class _Response:
                    content = [type("Block", (), {"text": '["Salute"]'})()]  # noqa: RUF012

                return _Response()

    transactions = [
        _txn("SPESA MISTERIOSA UNO", amount=-10.0),
        _txn("SPESA MISTERIOSA DUE", amount=-20.0),
    ]
    agent = CategorizerAgent(llm_client=_ShortResponseLLMClient())
    result = await agent.run(transactions)

    assert result[0].category == "Salute"
    # La seconda transazione non ha una risposta LLM corrispondente: deve ricevere il
    # fallback deterministico (Altro), non restare senza Categoria.
    assert result[1].category == "Altro"

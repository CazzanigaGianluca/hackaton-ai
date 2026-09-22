from datetime import date

from app.backend.agents.data_analyzer import compute_aggregates
from app.backend.models import Transaction, TransactionType


def _txn(d: date, description: str, amount: float, category: str) -> Transaction:
    return Transaction(
        date=d,
        description=description,
        amount=amount,
        type=TransactionType.ENTRATA if amount >= 0 else TransactionType.USCITA,
        category=category,
    )


TRANSACTIONS = [
    # Gennaio: 2000 di entrata, 100 alimentari, 200 ristorazione
    _txn(date(2025, 1, 6), "STIPENDIO", 2000.0, "Stipendio/Entrate"),  # lunedi
    _txn(date(2025, 1, 6), "CONAD", -100.0, "Alimentari"),  # lunedi
    _txn(date(2025, 1, 7), "RISTORANTE MARIO", -200.0, "Ristorazione"),  # martedi
    # Febbraio: 2000 di entrata, 100 alimentari, 300 ristorazione (trend in aumento)
    _txn(date(2025, 2, 6), "STIPENDIO", 2000.0, "Stipendio/Entrate"),  # giovedi
    _txn(date(2025, 2, 6), "CONAD", -100.0, "Alimentari"),  # giovedi
    _txn(date(2025, 2, 7), "RISTORANTE MARIO", -300.0, "Ristorazione"),  # venerdi
]

ISTAT = {
    "Alimentari": 19.2,
    "Abitazione e Utenze": 34.8,
    "Trasporti": 13.1,
    "Ristorazione": 8.3,
    "Abbigliamento": 6.1,
    "Intrattenimento": 5.8,
    "Salute": 4.2,
    "Shopping Online": 3.9,
    "Altro": 4.6,
}


def test_monthly_totals_split_entrate_uscite():
    result = compute_aggregates(TRANSACTIONS, istat_benchmarks=ISTAT)
    assert result["monthly_totals"]["2025-01"] == {"entrate": 2000.0, "uscite": 300.0}
    assert result["monthly_totals"]["2025-02"] == {"entrate": 2000.0, "uscite": 400.0}


def test_by_category_totals_sum_across_months():
    result = compute_aggregates(TRANSACTIONS, istat_benchmarks=ISTAT)
    assert result["by_category"]["Alimentari"]["total"] == 200.0
    assert result["by_category"]["Ristorazione"]["total"] == 500.0


def test_by_category_by_month_supports_trend_calculation():
    result = compute_aggregates(TRANSACTIONS, istat_benchmarks=ISTAT)
    ristorazione_by_month = result["by_category_by_month"]["Ristorazione"]
    assert ristorazione_by_month["2025-01"] == 200.0
    assert ristorazione_by_month["2025-02"] == 300.0


def test_top_merchants_sorted_by_total_spend_descending():
    result = compute_aggregates(TRANSACTIONS, istat_benchmarks=ISTAT)
    top = result["top_merchants"]
    assert top[0]["description"] == "RISTORANTE MARIO"
    assert top[0]["total"] == 500.0
    assert top[0]["count"] == 2


def test_heatmap_by_weekday_aggregates_expense_amounts():
    result = compute_aggregates(TRANSACTIONS, istat_benchmarks=ISTAT)
    heatmap = result["heatmap_by_weekday"]
    assert heatmap["Lunedì"] == 100.0
    assert heatmap["Martedì"] == 200.0
    assert heatmap["Giovedì"] == 100.0
    assert heatmap["Venerdì"] == 300.0


def test_savings_potential_only_includes_discretionary_categories():
    result = compute_aggregates(TRANSACTIONS, istat_benchmarks=ISTAT)
    assert set(result["savings_potential"].keys()).issubset(
        {"Ristorazione", "Intrattenimento", "Shopping Online"}
    )


def test_savings_potential_computes_delta_against_income():
    result = compute_aggregates(TRANSACTIONS, istat_benchmarks=ISTAT)
    ristorazione = result["savings_potential"]["Ristorazione"]
    # income osservato = 4000 (2000 + 2000); benchmark ISTAT Ristorazione = 8.3%
    # istat_amount = 4000 * 0.083 = 332; user_amount = 500 -> delta = 168
    assert ristorazione["istat_pct"] == 8.3
    assert round(ristorazione["delta_eur"], 2) == 168.0


def test_compute_aggregates_handles_empty_transaction_list():
    result = compute_aggregates([], istat_benchmarks=ISTAT)
    assert result["monthly_totals"] == {}
    assert result["by_category"] == {}
    assert result["top_merchants"] == []
    assert result["savings_potential"] == {}

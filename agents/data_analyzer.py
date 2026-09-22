"""Agent 3 - DataAnalyzer.

Calcola i Pattern di Spesa aggregati (per categoria, per mese, per merchant,
per giorno della settimana) e il Risparmio Potenziale rispetto ai Benchmark
ISTAT. Puramente deterministico: nessuna chiamata LLM, cosi' i numeri mostrati
in dashboard sono sempre riproducibili a partire dalle stesse Transazioni.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.backend.models import Transaction, TransactionType

_ISTAT_PATH = Path(__file__).resolve().parent.parent / "data" / "istat_benchmarks.json"

_WEEKDAY_NAMES_IT = [
    "Lunedì",
    "Martedì",
    "Mercoledì",
    "Giovedì",
    "Venerdì",
    "Sabato",
    "Domenica",
]

CATEGORY_TO_ISTAT_KEY = {
    "Alimentari": "Alimentari",
    "Utenze": "Abitazione e Utenze",
    "Trasporti": "Trasporti",
    "Ristorazione": "Ristorazione",
    "Abbigliamento": "Abbigliamento",
    "Intrattenimento": "Intrattenimento",
    "Salute": "Salute",
    "Shopping Online": "Shopping Online",
    "Altro": "Altro",
}

DISCRETIONARY_CATEGORIES = {"Ristorazione", "Intrattenimento", "Shopping Online"}


def _load_istat_benchmarks() -> dict[str, float]:
    with open(_ISTAT_PATH, encoding="utf-8") as f:
        return json.load(f)


def compute_aggregates(
    transactions: list[Transaction], istat_benchmarks: dict[str, float] | None = None
) -> dict:
    """Calcola tutti i Pattern di Spesa a partire dalle Transazioni categorizzate."""
    if istat_benchmarks is None:
        istat_benchmarks = _load_istat_benchmarks()

    monthly_totals: dict[str, dict[str, float]] = {}
    by_category_total: dict[str, float] = {}
    by_category_by_month: dict[str, dict[str, float]] = {}
    merchant_totals: dict[str, dict[str, float | int]] = {}
    heatmap_by_weekday: dict[str, float] = {name: 0.0 for name in _WEEKDAY_NAMES_IT}
    total_income = 0.0
    total_expenses = 0.0

    for t in transactions:
        month_key = f"{t.date.year:04d}-{t.date.month:02d}"
        monthly_totals.setdefault(month_key, {"entrate": 0.0, "uscite": 0.0})

        if t.type == TransactionType.ENTRATA:
            monthly_totals[month_key]["entrate"] += t.amount
            total_income += t.amount
            continue

        amount_abs = abs(t.amount)
        monthly_totals[month_key]["uscite"] += amount_abs
        total_expenses += amount_abs

        category = t.category or "Altro"
        by_category_total[category] = by_category_total.get(category, 0.0) + amount_abs
        by_category_by_month.setdefault(category, {})
        by_category_by_month[category][month_key] = (
            by_category_by_month[category].get(month_key, 0.0) + amount_abs
        )

        merchant_totals.setdefault(t.description, {"total": 0.0, "count": 0})
        merchant_totals[t.description]["total"] += amount_abs
        merchant_totals[t.description]["count"] += 1

        weekday_name = _WEEKDAY_NAMES_IT[t.date.weekday()]
        heatmap_by_weekday[weekday_name] += amount_abs

    by_category = {
        category: {
            "total": round(total, 2),
            "pct_of_expenses": round((total / total_expenses * 100), 2)
            if total_expenses
            else 0.0,
        }
        for category, total in by_category_total.items()
    }

    top_merchants = sorted(
        (
            {"description": desc, "total": round(v["total"], 2), "count": v["count"]}
            for desc, v in merchant_totals.items()
        ),
        key=lambda m: m["total"],
        reverse=True,
    )[:10]

    savings_potential = _compute_savings_potential(
        by_category_total, total_income, istat_benchmarks
    )

    return {
        "monthly_totals": monthly_totals,
        "by_category": by_category,
        "by_category_by_month": by_category_by_month,
        "top_merchants": top_merchants,
        "heatmap_by_weekday": {k: round(v, 2) for k, v in heatmap_by_weekday.items()},
        "savings_potential": savings_potential,
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
    }


def _compute_savings_potential(
    by_category_total: dict[str, float],
    total_income: float,
    istat_benchmarks: dict[str, float],
) -> dict[str, dict[str, float]]:
    """Risparmio Potenziale: delta tra spesa discrezionale effettiva e Benchmark
    ISTAT applicato al reddito osservato (vedi CONTEXT.md)."""
    if total_income <= 0:
        return {}

    savings: dict[str, dict[str, float]] = {}
    for category in DISCRETIONARY_CATEGORIES:
        istat_key = CATEGORY_TO_ISTAT_KEY.get(category, category)
        istat_pct = istat_benchmarks.get(istat_key)
        if istat_pct is None:
            continue

        user_amount = by_category_total.get(category, 0.0)
        istat_amount = total_income * istat_pct / 100
        user_pct = round((user_amount / total_income * 100), 2)
        delta_eur = round(user_amount - istat_amount, 2)

        savings[category] = {
            "user_pct": user_pct,
            "istat_pct": istat_pct,
            "delta_eur": delta_eur,
        }
    return savings


class DataAnalyzerAgent:
    """Wrapper agentico: chiama il tool `compute_aggregates` (nessun LLM)."""

    async def run(self, transactions: list[Transaction]) -> dict:
        return compute_aggregates(transactions)

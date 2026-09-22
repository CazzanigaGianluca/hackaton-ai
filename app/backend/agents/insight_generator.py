"""Agent 4 - InsightGenerator.

Trasforma i Pattern di Spesa (output di DataAnalyzer) in una lista strutturata
di Insight: {category, user_pct, istat_pct, trend, severity}. Usa Claude
Sonnet quando disponibile per una selezione piu' sfumata; altrimenti calcola
gli stessi campi con una regola deterministica (`generate_insights_fallback`),
cosi' la pipeline resta utilizzabile anche senza ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.backend.agents.data_analyzer import CATEGORY_TO_ISTAT_KEY
from app.backend.models import Insight

_ISTAT_PATH = Path(__file__).resolve().parents[3] / "data" / "istat_benchmarks.json"

MAX_INSIGHTS = 7


def _load_istat_benchmarks() -> dict[str, float]:
    with open(_ISTAT_PATH, encoding="utf-8") as f:
        return json.load(f)


def _severity_for_gap(gap: float) -> str:
    if gap >= 8:
        return "high"
    if gap >= 3:
        return "medium"
    return "low"


def _format_trend(month_totals: dict[str, float]) -> str:
    if len(month_totals) < 2:
        return "+0%"
    months_sorted = sorted(month_totals.keys())
    previous, last = month_totals[months_sorted[-2]], month_totals[months_sorted[-1]]
    if previous == 0:
        return "+0%"
    pct_change = round((last - previous) / previous * 100)
    sign = "+" if pct_change >= 0 else ""
    return f"{sign}{pct_change}%"


def generate_insights_fallback(
    analysis: dict, istat_benchmarks: dict[str, float] | None = None
) -> list[dict]:
    """Genera Insight deterministici confrontando ogni Categoria con il Benchmark ISTAT."""
    if istat_benchmarks is None:
        istat_benchmarks = _load_istat_benchmarks()

    by_category = analysis.get("by_category", {})
    by_category_by_month = analysis.get("by_category_by_month", {})

    insights = []
    for category, stats in by_category.items():
        istat_key = CATEGORY_TO_ISTAT_KEY.get(category)
        if istat_key is None or istat_key not in istat_benchmarks:
            continue

        user_pct = stats["pct_of_expenses"]
        istat_pct = istat_benchmarks[istat_key]
        gap = abs(user_pct - istat_pct)

        insights.append(
            {
                "category": category,
                "user_pct": user_pct,
                "istat_pct": istat_pct,
                "trend": _format_trend(by_category_by_month.get(category, {})),
                "severity": _severity_for_gap(gap),
                "_gap": gap,
            }
        )

    insights.sort(key=lambda i: i["_gap"], reverse=True)
    for insight in insights:
        del insight["_gap"]
    return insights[:MAX_INSIGHTS]


class InsightGeneratorAgent:
    """Wrapper agentico: usa Sonnet se disponibile, altrimenti il fallback deterministico."""

    def __init__(self, llm_client=None, model: str = "claude-sonnet-4-5"):
        self._llm_client = llm_client
        self._model = model

    async def run(self, analysis: dict) -> list[Insight]:
        raw_insights = await self._generate(analysis)
        return [Insight.model_validate(item) for item in raw_insights]

    async def _generate(self, analysis: dict) -> list[dict]:
        if self._llm_client is None:
            return generate_insights_fallback(analysis)

        fallback = generate_insights_fallback(analysis)
        response = await self._llm_client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=(
                "Sei un analista dati. Ricevi Pattern di Spesa e una lista di Insight "
                "candidati gia' calcolati deterministicamente. Seleziona e affina al massimo "
                f"{MAX_INSIGHTS} Insight (stessi campi: category, user_pct, istat_pct, trend, "
                "severity) in ordine di rilevanza educativa per l'utente. Rispondi SOLO con "
                "un array JSON."
            ),
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(
                        {"analysis": analysis, "candidates": fallback}
                    ),
                }
            ],
        )
        try:
            parsed = json.loads(response.content[0].text)
            # Valida la forma prima di sostituire il fallback deterministico: un JSON
            # sintatticamente valido ma con campi mancanti/severity fuori enum farebbe
            # fallire Insight.model_validate piu' avanti in run(), scartando insight
            # deterministici gia' buoni per un errore non recuperabile.
            for item in parsed:
                Insight.model_validate(item)
        except (
            json.JSONDecodeError,
            IndexError,
            AttributeError,
            TypeError,
            ValidationError,
        ):
            return fallback
        return parsed

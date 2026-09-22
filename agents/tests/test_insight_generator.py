from agents.insight_generator import InsightGeneratorAgent, generate_insights_fallback

ANALYSIS = {
    "by_category": {
        "Ristorazione": {"total": 500.0, "pct_of_expenses": 71.43},
        "Alimentari": {"total": 200.0, "pct_of_expenses": 28.57},
    },
    "by_category_by_month": {
        "Ristorazione": {"2025-01": 200.0, "2025-02": 300.0},
        "Alimentari": {"2025-01": 100.0, "2025-02": 100.0},
    },
}

ISTAT = {"Ristorazione": 8.3, "Alimentari": 19.2}


def test_generate_insights_fallback_returns_one_insight_per_comparable_category():
    insights = generate_insights_fallback(ANALYSIS, istat_benchmarks=ISTAT)
    categories = {i["category"] for i in insights}
    assert categories == {"Ristorazione", "Alimentari"}


def test_generate_insights_fallback_computes_trend_from_last_two_months():
    insights = generate_insights_fallback(ANALYSIS, istat_benchmarks=ISTAT)
    ristorazione = next(i for i in insights if i["category"] == "Ristorazione")
    assert ristorazione["trend"] == "+50%"

    alimentari = next(i for i in insights if i["category"] == "Alimentari")
    assert alimentari["trend"] == "+0%"


def test_generate_insights_fallback_assigns_high_severity_for_large_gap():
    insights = generate_insights_fallback(ANALYSIS, istat_benchmarks=ISTAT)
    ristorazione = next(i for i in insights if i["category"] == "Ristorazione")
    # 71.43% utente vs 8.3% ISTAT -> gap enorme
    assert ristorazione["severity"] == "high"


def test_generate_insights_fallback_sorted_by_gap_descending():
    insights = generate_insights_fallback(ANALYSIS, istat_benchmarks=ISTAT)
    assert insights[0]["category"] == "Ristorazione"


def test_generate_insights_fallback_handles_empty_analysis():
    insights = generate_insights_fallback(
        {"by_category": {}, "by_category_by_month": {}}, istat_benchmarks=ISTAT
    )
    assert insights == []


async def test_insight_generator_agent_falls_back_when_llm_json_has_invalid_schema():
    class _InvalidSchemaLLMClient:
        class messages:
            @staticmethod
            async def create(**kwargs):
                # JSON sintatticamente valido ma con severity fuori dall'enum consentito:
                # non deve rompere la pipeline scartando il fallback deterministico.
                class _Response:
                    content = [  # noqa: RUF012
                        type(
                            "Block",
                            (),
                            {
                                "text": (
                                    '[{"category": "Ristorazione", '
                                    '"severity": "urgentissimo"}]'
                                )
                            },
                        )()
                    ]

                return _Response()

    agent = InsightGeneratorAgent(llm_client=_InvalidSchemaLLMClient())
    insights = await agent.run(
        {
            "by_category": {"Ristorazione": {"total": 500.0, "pct_of_expenses": 71.43}},
            "by_category_by_month": {},
        }
    )

    assert len(insights) == 1
    assert insights[0].category == "Ristorazione"
    assert insights[0].severity == "high"

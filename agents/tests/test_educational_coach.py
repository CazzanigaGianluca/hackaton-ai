from agents.educational_coach import (
    DEFLECTION_MESSAGE,
    EducationalCoachAgent,
    is_investment_advice_request,
)
from app.backend.models import Insight


def test_flags_direct_investment_question():
    assert (
        is_investment_advice_request("dove dovrei investire i miei risparmi?") is True
    )


def test_flags_stock_purchase_request():
    assert (
        is_investment_advice_request("quali azioni dovrei comprare questo mese?")
        is True
    )


def test_flags_fund_recommendation_request():
    assert is_investment_advice_request("mi consigli un fondo di investimento?") is True


def test_flags_cryptocurrency_question():
    assert (
        is_investment_advice_request("conviene comprare criptovalute adesso?") is True
    )


def test_does_not_flag_generic_budgeting_question():
    assert (
        is_investment_advice_request("come posso risparmiare sulla ristorazione?")
        is False
    )


def test_does_not_flag_question_about_spending_pattern():
    assert (
        is_investment_advice_request("perche' spendo cosi' tanto in abbonamenti?")
        is False
    )


def test_deflection_message_does_not_contain_prescriptive_advice():
    forbidden_phrases = ["dovresti investire", "ti consiglio di comprare", "vendi"]
    lowered = DEFLECTION_MESSAGE.lower()
    assert not any(phrase in lowered for phrase in forbidden_phrases)


def test_does_not_flag_action_plan_phrase_with_apostrophe():
    # "d'azione" (singolare, con apostrofo prima) non deve essere confuso con le
    # azioni di borsa: solo il plurale "azioni" e' considerato un segnale finanziario.
    assert (
        is_investment_advice_request("vorrei un piano d'azione per risparmiare")
        is False
    )


def test_does_not_flag_academic_or_investigative_titoli_and_investigazione():
    assert (
        is_investment_advice_request(
            "quali titoli di studio servono per questo lavoro?"
        )
        is False
    )
    assert (
        is_investment_advice_request(
            "mi hanno chiesto di fare un'investigazione sulle spese"
        )
        is False
    )


async def test_educational_coach_falls_back_when_llm_response_has_no_text_block():
    class _EmptyContentLLMClient:
        class messages:
            @staticmethod
            async def create(**kwargs):
                class _Response:
                    content: list = []  # noqa: RUF012

                return _Response()

    agent = EducationalCoachAgent(llm_client=_EmptyContentLLMClient())
    insights = [
        Insight(
            category="Ristorazione",
            user_pct=20.0,
            istat_pct=8.3,
            trend="+5%",
            severity="high",
        )
    ]

    reply = await agent.run(insights)
    assert "Ristorazione" in reply

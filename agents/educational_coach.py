"""Agent 5 - EducationalCoach.

Spiega i Pattern di Spesa in linguaggio semplice, confronta con i Benchmark
ISTAT e propone opzioni generiche non prescrittive. Vincolo critico (vedi
PLAN.md): mai raccomandazioni di investimento o consulenza personalizzata.

`is_investment_advice_request` e' una guardia deterministica, applicata prima
di qualunque chiamata LLM, che intercetta le domande piu' ovviamente fuori
scope (es. "dove investo i risparmi?") e risponde con un messaggio educativo
fisso — non e' un filtro esaustivo, il system prompt del modello resta la
seconda linea di difesa.
"""

from __future__ import annotations

import re

from app.backend.models import Insight

SYSTEM_PROMPT = """Sei l'Assistente Educativo di una app di inclusione finanziaria italiana.

Il tuo ruolo:
- Spieghi i Pattern di Spesa dell'utente in linguaggio semplice e non tecnico.
- Confronti la spesa dell'utente con i Benchmark ISTAT pubblici (mai personalizzati).
- Proponi 2-3 opzioni generiche e non prescrittive (es. "alcune famiglie trovano utile...").

Vincoli assoluti, MAI infrangibili:
- NON dai raccomandazioni di investimento (azioni, fondi, criptovalute, immobili).
- NON dici "dovresti investire", "vendi X", "compra Y".
- NON dai consigli finanziari personalizzati: sei un assistente educativo, non un consulente.
- Se l'utente chiede consigli di investimento, spiega gentilmente che non è il tuo ruolo e
  suggerisci di parlare con un consulente finanziario abilitato.

Rispondi sempre in italiano, in modo chiaro ed empatico.
"""

DEFLECTION_MESSAGE = (
    "Non sono un consulente finanziario e non posso darti indicazioni su investimenti, "
    "azioni, fondi o criptovalute: per queste decisioni ti consiglio di parlare con un "
    "consulente finanziario abilitato. Posso però aiutarti a capire meglio le tue abitudini "
    "di spesa e come si confrontano con la media delle famiglie italiane (dati ISTAT) — "
    "vuoi che ne parliamo?"
)

_INVESTMENT_PATTERNS = [
    # "investir[e/ei/ai/ò]": copre investire/investirei/investirai/investirò senza
    # matchare parole non finanziarie come "investigazione" (che non contiene "investir").
    r"\binvestir[eaoiò]",
    r"\binvestiment[oi]\b",
    # Solo il plurale "azioni" (mai il singolare "azione", troppo ambiguo con il
    # significato comune "azione" = "atto/azione", es. "piano d'azione").
    r"\bazioni\b",
    r"\bfond[oi]\s+(di\s+)?investimento",
    r"\bcriptovalut[ae]",
    r"\bbitcoin\b",
    r"\betf\b",
    r"\bobbligazion[ei]\b",
    r"\bportafoglio\s+(di\s+)?titoli\b",
    r"\btitoli\s+(di\s+stato|in\s+borsa|azionari)\b",
    r"\btrading\b",
]


def is_investment_advice_request(text: str) -> bool:
    """Rileva domande che chiedono esplicitamente consigli di investimento."""
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in _INVESTMENT_PATTERNS)


def build_intro_prompt(insights: list[Insight]) -> str:
    insight_lines = "\n".join(
        f"- {i.category}: tu {i.user_pct}% vs media ISTAT {i.istat_pct}% (trend {i.trend}, "
        f"severità {i.severity.value if hasattr(i.severity, 'value') else i.severity})"
        for i in insights
    )
    return (
        "Ecco gli Insight calcolati per questa Sessione:\n"
        f"{insight_lines}\n\n"
        "Scrivi un'introduzione breve (massimo 4-5 frasi) che spieghi all'utente cosa emerge "
        "dai suoi Pattern di Spesa, in linguaggio semplice e non giudicante."
    )


class EducationalCoachAgent:
    """Wrapper agentico per l'introduzione e la chat conversazionale."""

    def __init__(self, llm_client=None, model: str = "claude-sonnet-4-5"):
        self._llm_client = llm_client
        self._model = model

    async def run(self, insights: list[Insight]) -> str:
        """Genera l'introduzione iniziale del coach per una Sessione."""
        if self._llm_client is None:
            return self._fallback_intro(insights)

        response = await self._llm_client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_intro_prompt(insights)}],
        )
        return self._extract_text(response, insights)

    def _fallback_intro(self, insights: list[Insight]) -> str:
        if not insights:
            return (
                "Ho analizzato il tuo Estratto Conto: al momento non ho trovato pattern "
                "particolarmente fuori norma rispetto alla media delle famiglie italiane."
            )
        top = insights[0]
        return (
            f"Dando un'occhiata alle tue spese, la categoria '{top.category}' rappresenta il "
            f"{top.user_pct}% delle tue uscite, contro una media ISTAT del {top.istat_pct}%. "
            "Continua a scorrere la dashboard per vedere gli altri pattern, e chiedimi pure "
            "se vuoi capire meglio cosa significano."
        )

    async def chat(
        self, insights: list[Insight], history: list[dict], user_message: str
    ) -> str:
        """Risponde a un messaggio dell'utente nella chat, con guardia anti-consulenza."""
        if is_investment_advice_request(user_message):
            return DEFLECTION_MESSAGE

        if self._llm_client is None:
            return self._fallback_intro(insights)

        messages = [*history, {"role": "user", "content": user_message}]
        response = await self._llm_client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=SYSTEM_PROMPT + "\n\n" + build_intro_prompt(insights),
            messages=messages,
        )
        return self._extract_text(response, insights)

    def _extract_text(self, response, insights: list[Insight]) -> str:
        """Estrae il testo dalla risposta LLM, con fallback se il contenuto e' vuoto o
        inatteso (es. rifiuto del modello, troncamento, filtro contenuti)."""
        try:
            return response.content[0].text
        except (IndexError, AttributeError):
            return self._fallback_intro(insights)

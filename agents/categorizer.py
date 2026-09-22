"""Agent 2 - Categorizer.

Assegna una Categoria a ogni Transazione. Il percorso rapido e deterministico
e' un lookup per keyword (`data/categories.json`); i casi ambigui (nessun
match) vengono risolti da Claude Haiku quando disponibile, altrimenti con una
regola di fallback (Entrata non matchata -> Stipendio/Entrate, Uscita non
matchata -> Altro).
"""

from __future__ import annotations

import json
from pathlib import Path

from app.backend.models import Category, Transaction, TransactionType

_CATEGORIES_PATH = Path(__file__).resolve().parent.parent / "data" / "categories.json"


def _load_keyword_map() -> dict[str, list[str]]:
    with open(_CATEGORIES_PATH, encoding="utf-8") as f:
        return json.load(f)


_KEYWORD_MAP = _load_keyword_map()


def classify_by_keyword(
    description: str, transaction_type: TransactionType | None = None
) -> str | None:
    """Ritorna la prima Categoria le cui keyword compaiono nella descrizione, o None.

    Se `transaction_type` e' Uscita, la Categoria 'Stipendio/Entrate' non viene mai
    assegnata via keyword: un pagamento in uscita non e' mai un'entrata, anche se la
    descrizione contiene parole come 'RIMBORSO' (usate anche da banche per commissioni
    o penali in uscita).
    """
    upper_description = description.upper()
    for category, keywords in _KEYWORD_MAP.items():
        if (
            category == "Stipendio/Entrate"
            and transaction_type == TransactionType.USCITA
        ):
            continue
        for keyword in keywords:
            if keyword in upper_description:
                return category
    return None


def _fallback_category(transaction: Transaction) -> str:
    if transaction.type == TransactionType.ENTRATA:
        return "Stipendio/Entrate"
    return "Altro"


def categorize_transactions(transactions: list[Transaction]) -> list[Transaction]:
    """Categorizza deterministicamente via keyword, con fallback per i casi ambigui."""
    categorized: list[Transaction] = []
    for transaction in transactions:
        category = classify_by_keyword(
            transaction.description, transaction.type
        ) or _fallback_category(transaction)
        categorized.append(
            transaction.model_copy(update={"category": Category(category)})
        )
    return categorized


class CategorizerAgent:
    """Wrapper agentico: lookup deterministico + risoluzione LLM per i casi ambigui."""

    def __init__(self, llm_client=None, model: str = "claude-haiku-4-5-20251001"):
        self._llm_client = llm_client
        self._model = model

    async def run(self, transactions: list[Transaction]) -> list[Transaction]:
        pending: list[int] = []
        result = list(transactions)
        for i, transaction in enumerate(transactions):
            category = classify_by_keyword(transaction.description, transaction.type)
            if category is not None:
                result[i] = transaction.model_copy(
                    update={"category": Category(category)}
                )
            else:
                pending.append(i)

        if pending and self._llm_client is not None:
            resolved = await self._classify_ambiguous_with_llm(
                [transactions[i].description for i in pending]
            )
            # Un LLM che risponde con un array piu' corto/lungo del previsto non deve
            # lasciare Transazioni senza Categoria: si applica il fallback deterministico
            # a ogni indice per cui non è arrivata una risposta valida.
            resolved_by_index = dict(zip(pending, resolved))
            for idx in pending:
                category = resolved_by_index.get(idx)
                final_category = category or _fallback_category(transactions[idx])
                result[idx] = transactions[idx].model_copy(
                    update={"category": Category(final_category)}
                )
        else:
            for idx in pending:
                result[idx] = transactions[idx].model_copy(
                    update={"category": Category(_fallback_category(transactions[idx]))}
                )
        return result

    async def _classify_ambiguous_with_llm(
        self, descriptions: list[str]
    ) -> list[str | None]:
        import json as _json

        valid_categories = list(_KEYWORD_MAP.keys())
        response = await self._llm_client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=(
                "Classifica ogni descrizione bancaria in UNA delle categorie: "
                f"{valid_categories}. Rispondi SOLO con un array JSON di stringhe, "
                "una categoria per ogni descrizione, nello stesso ordine."
            ),
            messages=[{"role": "user", "content": _json.dumps(descriptions)}],
        )
        try:
            categories = _json.loads(response.content[0].text)
        except (json.JSONDecodeError, IndexError):
            return [None] * len(descriptions)
        return [c if c in valid_categories else None for c in categories]

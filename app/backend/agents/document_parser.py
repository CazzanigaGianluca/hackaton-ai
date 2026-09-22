"""Agent 1 - DocumentParser.

Estrae la lista di Transazioni da un Estratto Conto (CSV o PDF). Il parsing e'
deterministico (nessuna chiamata LLM) per i formati CSV/PDF strutturati noti
(stile Intesa Sanpaolo/Fineco); se l'estrazione deterministica non produce
alcuna Transazione, ricorre a Claude Haiku come fallback su testo libero.
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime

from app.backend.models import Transaction, TransactionType

REQUIRED_COLUMNS = {"data", "descrizione", "importo"}


def _parse_italian_date(raw: str) -> date:
    return datetime.strptime(raw.strip(), "%d/%m/%Y").date()  # noqa: DTZ007 - solo la data


def _parse_amount(raw: str) -> float:
    """Converte un importo testuale (es. '-85.40', '+2.800,00', '-4,50') in float."""
    cleaned = raw.strip().replace(" ", "")
    if not cleaned:
        raise ValueError("importo vuoto")

    sign = ""
    if cleaned[0] in "+-":
        sign = "-" if cleaned[0] == "-" else ""
        cleaned = cleaned[1:]

    if "," in cleaned:
        # Formato italiano: punto = separatore migliaia, virgola = decimali.
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "." in cleaned and len(cleaned.split(".")[-1]) == 3:
        # Nessuna virgola e l'ultimo gruppo ha 3 cifre: gli importi in EUR hanno al
        # massimo 2 decimali, quindi il punto e' separatore delle migliaia (es. "1.200"
        # = 1200, non 1.2) e non un separatore decimale.
        cleaned = cleaned.replace(".", "")

    return float(f"{sign}{cleaned}")


def _row_to_transaction(
    date_raw: str, description_raw: str, amount_raw: str, source_file: str | None
) -> Transaction:
    amount = _parse_amount(amount_raw)
    return Transaction(
        date=_parse_italian_date(date_raw),
        description=description_raw.strip(),
        amount=amount,
        type=TransactionType.ENTRATA if amount >= 0 else TransactionType.USCITA,
        source_file=source_file,
    )


def parse_csv(content: str, source_file: str | None = None) -> list[Transaction]:
    """Parsa un CSV stile Intesa Sanpaolo: colonne Data, Descrizione, Importo, Valuta.

    Rileva automaticamente il delimitatore (',' o ';'): alcuni export bancari
    italiani usano ';' per poter usare la virgola come separatore decimale.
    """
    first_line = content.split("\n", 1)[0]
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    if reader.fieldnames is None:
        return []

    header_lower = {(name or "").strip().lower() for name in reader.fieldnames}
    if not REQUIRED_COLUMNS.issubset(header_lower):
        raise ValueError(
            f"CSV non riconosciuto: colonne richieste {REQUIRED_COLUMNS}, trovate {header_lower}"
        )

    column_map = {(name or "").strip().lower(): name for name in reader.fieldnames}

    transactions: list[Transaction] = []
    for row in reader:
        try:
            transactions.append(
                _row_to_transaction(
                    row[column_map["data"]],
                    row[column_map["descrizione"]],
                    row[column_map["importo"]],
                    source_file,
                )
            )
        except (ValueError, TypeError, KeyError, AttributeError):
            continue
    return transactions


def extract_transactions_from_rows(
    rows: list[list[str | None]], source_file: str | None = None
) -> list[Transaction]:
    """Converte righe di tabella (es. estratte da pdfplumber) in Transazioni.

    Salta la riga di header e qualunque riga vuota o non conforme.
    """
    transactions: list[Transaction] = []
    for row in rows:
        cells = [c.strip() if isinstance(c, str) else c for c in row]
        if len(cells) < 3 or not cells[0]:
            continue
        if str(cells[0]).strip().lower() == "data":
            continue
        try:
            transactions.append(
                _row_to_transaction(
                    str(cells[0]), str(cells[1]), str(cells[2]), source_file
                )
            )
        except (ValueError, TypeError, IndexError):
            continue
    return transactions


def parse_pdf(file_bytes: bytes, source_file: str | None = None) -> list[Transaction]:
    """Estrae le Transazioni da un Estratto Conto PDF usando pdfplumber."""
    import pdfplumber

    transactions: list[Transaction] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                transactions.extend(extract_transactions_from_rows(table, source_file))
    return transactions


class DocumentParserAgent:
    """Orchestratore del parsing: dispatcha per estensione e applica il fallback LLM."""

    def __init__(self, llm_client=None, model: str = "claude-haiku-4-5-20251001"):
        self._llm_client = llm_client
        self._model = model

    async def run(self, files: list[tuple[str, bytes]]) -> list[Transaction]:
        """files: lista di (filename, contenuto raw bytes)."""
        transactions: list[Transaction] = []
        for filename, content in files:
            transactions.extend(await self._parse_one(filename, content))
        return transactions

    async def _parse_one(self, filename: str, content: bytes) -> list[Transaction]:
        lower_name = filename.lower()
        if lower_name.endswith(".csv"):
            parsed = parse_csv(
                content.decode("utf-8", errors="replace"), source_file=filename
            )
        elif lower_name.endswith(".pdf"):
            parsed = parse_pdf(content, source_file=filename)
        else:
            parsed = []

        if parsed:
            return parsed

        if self._llm_client is not None:
            return await self._parse_with_llm_fallback(filename, content)
        return []

    async def _parse_with_llm_fallback(
        self, filename: str, content: bytes
    ) -> list[Transaction]:
        """Fallback: chiede a Claude Haiku di estrarre le transazioni da testo libero."""
        import json

        text = content.decode("utf-8", errors="replace")
        response = await self._llm_client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=(
                "Estrai le transazioni bancarie dal testo fornito. Rispondi SOLO con un array "
                "JSON di oggetti {date: 'YYYY-MM-DD', description: str, amount: float}. "
                "Nessun testo aggiuntivo."
            ),
            messages=[{"role": "user", "content": text[:8000]}],
        )
        try:
            items = json.loads(response.content[0].text)
        except (json.JSONDecodeError, IndexError, AttributeError):
            return []

        transactions = []
        for item in items:
            try:
                amount = float(item["amount"])
                transactions.append(
                    Transaction(
                        date=item["date"],
                        description=str(item["description"]).strip(),
                        amount=amount,
                        type=TransactionType.ENTRATA
                        if amount >= 0
                        else TransactionType.USCITA,
                        source_file=filename,
                    )
                )
            except (KeyError, ValueError, TypeError):
                continue
        return transactions

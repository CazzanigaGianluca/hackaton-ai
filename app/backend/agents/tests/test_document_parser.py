import pytest

from app.backend.agents.document_parser import extract_transactions_from_rows, parse_csv

SAMPLE_CSV = """Data,Descrizione,Importo,Valuta
15/01/2025,CONAD SUPERMERCATI,-85.40,EUR
15/01/2025,STIPENDIO ACCENTURE,+2800.00,EUR
16/01/2025,NETFLIX ABBONAMENTO,-17.99,EUR
"""


def test_parse_csv_returns_one_transaction_per_row():
    transactions = parse_csv(SAMPLE_CSV)
    assert len(transactions) == 3


def test_parse_csv_infers_type_from_amount_sign():
    transactions = parse_csv(SAMPLE_CSV)
    assert transactions[0].type == "uscita"
    assert transactions[0].amount == -85.40
    assert transactions[1].type == "entrata"
    assert transactions[1].amount == 2800.00


def test_parse_csv_parses_italian_date_format():
    transactions = parse_csv(SAMPLE_CSV)
    assert transactions[0].date.isoformat() == "2025-01-15"


def test_parse_csv_accepts_semicolon_delimiter_with_comma_decimal():
    csv_content = "Data;Descrizione;Importo;Valuta\n01/02/2025;BAR CENTRALE;-4,50;EUR\n"
    transactions = parse_csv(csv_content)
    assert transactions[0].amount == -4.50


def test_parse_csv_treats_dot_as_thousands_separator_when_no_comma_present():
    # "-1.200" senza virgola: le 3 cifre dopo il punto escludono che sia un decimale
    # (una valuta EUR ha al massimo 2 decimali) quindi e' -1200.0, non -1.2.
    csv_content = (
        "Data,Descrizione,Importo,Valuta\n01/02/2025,AFFITTO CASA,-1.200,EUR\n"
    )
    transactions = parse_csv(csv_content)
    assert transactions[0].amount == -1200.0


def test_parse_csv_sets_source_file():
    transactions = parse_csv(SAMPLE_CSV, source_file="estratto_gennaio_2025.csv")
    assert all(t.source_file == "estratto_gennaio_2025.csv" for t in transactions)


def test_parse_csv_skips_malformed_rows_without_failing():
    csv_content = (
        "Data,Descrizione,Importo,Valuta\n"
        "15/01/2025,CONAD SUPERMERCATI,-85.40,EUR\n"
        "DATA-NON-VALIDA,DESCRIZIONE ROTTA,non-un-numero,EUR\n"
        "16/01/2025,NETFLIX ABBONAMENTO,-17.99,EUR\n"
    )
    transactions = parse_csv(csv_content)
    assert len(transactions) == 2


def test_parse_csv_raises_on_missing_required_columns():
    csv_content = "Colonna1,Colonna2\nA,B\n"
    with pytest.raises(ValueError):
        parse_csv(csv_content)


def test_extract_transactions_from_rows_skips_header_row():
    rows = [
        ["Data", "Descrizione", "Importo", "Valuta"],
        ["15/01/2025", "CONAD SUPERMERCATI", "-85.40", "EUR"],
    ]
    transactions = extract_transactions_from_rows(rows)
    assert len(transactions) == 1
    assert transactions[0].description == "CONAD SUPERMERCATI"


def test_extract_transactions_from_rows_ignores_empty_rows():
    rows = [
        ["Data", "Descrizione", "Importo", "Valuta"],
        [],
        ["15/01/2025", "CONAD SUPERMERCATI", "-85.40", "EUR"],
        [None, None, None, None],
    ]
    transactions = extract_transactions_from_rows(rows)
    assert len(transactions) == 1

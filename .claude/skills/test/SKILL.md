---
name: test
description: "Genera unit test per un modulo Python del progetto, li esegue con pytest e itera fino a farli passare (max 3 tentativi). Usa stub LLM inline (non unittest.mock), pytest-asyncio in auto mode, test co-locati in */tests/."
argument-hint: "<file o modulo da testare>"
---

# test

Genera unit test per un modulo, li esegue con pytest, e corregge fino a farli passare (max 3 iterazioni).

## 1. Leggi il modulo target

Leggi il file indicato per capire:
- Quali funzioni/metodi pubblici esistono
- Quali dipendenze esterne ha (LLM client, SQLite, filesystem)
- Quali casi limite emergono dalla logica (lista vuota, input None, LLM che restituisce meno risultati del previsto)

## 2. Determina il path del file di test

- Per `app/backend/agents/foo.py` → `app/backend/agents/tests/test_foo.py`
- Per `app/backend/foo.py` → `app/backend/tests/test_foo.py`
- Se la directory `tests/` non esiste, creala con un `__init__.py` vuoto

## 3. Scrivi i test seguendo i pattern del progetto

**Pattern stub LLM inline** (obbligatorio, non usare `unittest.mock`):

```python
class _FakeLLMClient:
    class messages:
        @staticmethod
        async def create(**kwargs):
            class _Response:
                content = [type("Block", (), {"text": '...'})()]
            return _Response()
```

**Regole**:
- `from __future__ import annotations` in testa
- pytest-asyncio è in modalità `auto`: le coroutine async sono test nativi, nessun decorator `@pytest.mark.asyncio`
- Helper factory per i dati di test (pattern `_txn()`, `_session()`, ecc.) definiti in testa al file
- Un test per comportamento — nomi descrittivi: `test_<cosa>_quando_<condizione>()`
- Testa il fallback deterministico (`llm_client=None`) separatamente dalla path LLM
- Non fare assert su dettagli di implementazione interni: testa l'output pubblico

**Copertura minima**:
- Happy path principale
- Fallback deterministico (se agente)
- Almeno un edge case (input vuoto, LLM risponde meno elementi del previsto, ecc.)

## 4. Esegui i test

```bash
python -m pytest <path/test_file.py> -v
```

## 5. Itera se falliscono (max 3 tentativi)

Per ogni iterazione:
1. Leggi l'output di pytest
2. Identifica la causa del fallimento (import error, assertion wrong, fixture mancante)
3. Correggi il file di test (non il file sorgente, a meno che il bug sia nel sorgente)
4. Riesegui

**Dopo il 3° tentativo fallito**: fermati, mostra l'output di pytest e spiega cosa blocca il fix.

## 6. Riporta il risultato finale

- Numero di test generati e passati
- Path del file di test creato
- Se ci sono test ancora rossi dopo 3 iterazioni, elencali con la causa

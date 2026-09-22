# Skill: generate

Genera codice Python per questo progetto a partire da una descrizione in linguaggio naturale.

## Come invocare

```
/generate <descrizione di cosa creare>
```

Esempio: `/generate agente che recupera le ultime 5 Transazioni per Categoria da SQLite`

## Procedura

1. **Leggi il contesto del dominio** da `CONTEXT.md` prima di scrivere una riga di codice. Usa i termini esatti del glossario (Transazione, Sessione, Categoria, Estratto Conto, Insight…). Non inventare sinonimi.

2. **Determina il tipo di componente** dalla descrizione:
   - **Agente**: va in `agents/`, segue il pattern class-based (vedi sotto)
   - **Endpoint FastAPI**: va in `app/backend/`, usa `APIRouter`
   - **Modello Pydantic**: va in `app/backend/models.py`
   - **Utility / funzione pura**: va nel modulo più vicino al suo uso

3. **Pattern agente obbligatorio**:
   ```python
   from __future__ import annotations

   class NomeAgent:
       def __init__(self, llm_client=None) -> None:
           self._llm = llm_client

       async def run(self, input: TipoInput) -> TipoOutput:
           if self._llm is None:
               return self._fallback_deterministico(input)
           # chiamata LLM
   ```
   - Tipizzazione completa su tutti i parametri e valori di ritorno
   - Fallback deterministico obbligatorio quando `llm_client is None`
   - Il client LLM è sempre iniettato, mai importato direttamente nell'agente

4. **Sicurezza**:
   - Non loggare mai importi, descrizioni di Transazioni, o dati di Sessione
   - Non esporre `ANTHROPIC_API_KEY` in output, log, o eccezioni
   - Non concatenare input utente in f-string di prompt senza sanitizzazione

5. **Scrivi il file** nel path corretto e mostra il path completo.

6. **Dopo aver scritto**, esegui `ruff check <file> --fix` e `ruff format <file>` per rispettare le convenzioni di stile del progetto (`ruff.toml` è alla root).

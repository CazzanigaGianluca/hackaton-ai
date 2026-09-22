---
name: generate
description: "Genera codice per questo progetto da una descrizione in linguaggio naturale. Per il frontend (Next.js 14 / React 18) invoca ui-ux-pro-max per design system e best practice prima di scrivere qualsiasi componente. Per il backend applica il pattern agente con llm_client=None e fallback deterministico."
argument-hint: "<descrizione di cosa creare>"
---

# generate

Genera codice per questo progetto a partire da una descrizione in linguaggio naturale.
Per il frontend (Next.js 14 / React 18) usa la skill `ui-ux-pro-max` prima di scrivere qualsiasi componente.
Per il backend (FastAPI / agenti Python) applica le convenzioni del progetto direttamente.

## Identifica il tipo di componente

Dalla descrizione, determina se la richiesta è:

| Tipo | Parole chiave | Vai a |
|---|---|---|
| **Frontend** | pagina, componente, card, form, dashboard, UI, modal, grafico, chart, layout, schermata | Sezione Frontend |
| **Agente Python** | agente, pipeline, analisi, parsing, LLM, coach, categorizer | Sezione Backend – Agente |
| **Endpoint FastAPI** | route, API, endpoint, POST, GET, SSE | Sezione Backend – Endpoint |
| **Modello / utility** | model, schema, Pydantic, funzione pura, helper | Sezione Backend – Utility |

---

## Sezione Frontend (Next.js 14 / React 18)

### 1. Analizza i requisiti

Estrai dalla descrizione:
- **Tipo di componente**: pagina intera, componente riusabile, sezione, chart, form
- **Dati visualizzati**: Transazioni, Insight, Pattern di Spesa, Sessione, Benchmark ISTAT
- **Interattività**: statico, click, form, SSE streaming, chat

### 2. Esegui il design system con `ui-ux-pro-max`

**Per nuove pagine o sezioni significative** — esegui `--design-system`:

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "fintech personal finance education dashboard" --design-system -p "Inclusione Finanziaria" --density 7
```

**Per singoli componenti** — esegui una ricerca mirata con `--domain`:

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain product
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain chart
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain ux
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain icons
```

**Sempre** — esegui la ricerca stack-specifica:

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --stack nextjs
```

### 3. Applica le regole di qualità obbligatorie

- Contrasto testo ≥ 4.5:1 (`color-contrast`)
- Touch target ≥ 44×44px (`touch-target-size`)
- Focus ring visibile su tutti gli elementi interattivi (`focus-states`)
- Nessuna emoji come icona: usa Phosphor (`@phosphor-icons/react`) o Lucide (`no-emoji-icons`)
- `aria-label` su icon-button senza testo visibile (`aria-labels`)
- Loading feedback su operazioni async (`loading-buttons`)

### 4. Convenzioni del progetto FE

- **Stack**: Next.js 14 App Router, React 18, TypeScript
- **Stile**: Tailwind CSS
- **Path componenti riusabili**: `app/frontend/src/components/`
- **Path pagine**: `app/frontend/src/app/`
- **Path utility**: `app/frontend/src/lib/`
- SSE verso `POST /api/analyze` — usa `fetch` con `ReadableStream`
- Chat verso `POST /api/coach/{session_id}` — payload `{ message: string }`
- Termini di dominio dal `CONTEXT.md`: Transazione, Sessione, Categoria, Insight, Pattern di Spesa

### 5. Scrivi il componente

Genera il codice integrando le indicazioni del design system. Mostra il path completo del file creato.

### 6. Post-generazione FE

```bash
cd app/frontend && npx tsc --noEmit
```

---

## Sezione Backend – Agente Python

### 1. Pattern agente obbligatorio

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
- Path: `app/backend/agents/`

### 2. Sicurezza

- Non loggare mai importi, descrizioni di Transazioni, o dati di Sessione
- Non esporre `ANTHROPIC_API_KEY` in output, log, o eccezioni
- Non concatenare input utente in f-string di prompt senza sanitizzazione

### 3. Post-generazione BE

```bash
ruff check <file> --fix && ruff format <file>
```

---

## Sezione Backend – Endpoint FastAPI

- Path: `app/backend/routes/`
- Usa `APIRouter`, non `FastAPI` direttamente
- Inietta `get_llm_client()` per ogni richiesta (non al module level)
- Risposte SSE: `StreamingResponse` con `media_type="text/event-stream"`

---

## Sezione Backend – Utility / Modello

- Modelli Pydantic: aggiungi a `app/backend/models.py`, usando i nomi dal `CONTEXT.md`
- Funzioni pure (no I/O): collocale nel modulo più vicino al loro utilizzo
- Helper database: aggiungi a `app/backend/database.py`, con `db_path: str | None = None` per testabilità

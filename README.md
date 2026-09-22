# Inclusione Finanziaria

Una famiglia italiana carica il proprio Estratto Conto (CSV o PDF) e ottiene una dashboard
che categorizza le spese, le confronta con i Benchmark ISTAT e le spiega tramite un
Assistente Educativo — mai un consulente finanziario, mai raccomandazioni di investimento.

Vedi `PLAN.md` per l'architettura completa, `CONTEXT.md` per il glossario di dominio e
`docs/adr/` per le decisioni tecniche.

## Struttura

```
agents/            # I 5 agenti della pipeline + orchestrator (Python, no framework)
app/backend/        # FastAPI: routes, database (SQLite)
app/frontend/        # Next.js 14 + Tailwind + Recharts
data/               # categories.json, istat_benchmarks.json, estratti conto di esempio
docs/adr/           # Decisioni architetturali
```

## Backend

Richiede Python 3.12 (nell'ambiente di sviluppo locale usato per questa implementazione era
disponibile solo Python 3.9: funziona comunque grazie a `eval_type_backport` in
`requirements.txt`, ma su Railway verrà usato 3.12 come da `.python-version`).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Facoltativo: senza ANTHROPIC_API_KEY gli agenti Sonnet (InsightGenerator,
# EducationalCoach) usano un fallback deterministico — utile per sviluppo/demo offline.
export ANTHROPIC_API_KEY=sk-...

uvicorn app.backend.main:app --reload --port 8000
```

Test:

```bash
pytest        # test: agenti, orchestrator, database, route FastAPI
```

## Frontend

```bash
cd app/frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL punta al backend
npm run dev
```

Apri `http://localhost:3000`, carica uno o più file da `data/sample/`, verrai reindirizzato
alla dashboard.

## Verifiche end-to-end effettuate

- `pytest` su parsing CSV/PDF, categorizzazione, aggregati, insight, guardia
  anti-consulenza del coach, persistenza SQLite, route FastAPI.
- Pipeline completa testata offline (senza `ANTHROPIC_API_KEY`) sui 3 CSV di esempio in
  `data/sample/`: categorizzazione corretta, aggregati coerenti, insight generati, intro del
  coach generata.
- `POST /api/analyze` con i 3 CSV di esempio via `curl`: stream SSE con i 5 stage, sessione
  persistita, `GET /api/session/{id}` e `POST /api/coach/{id}` verificati (inclusa la
  deflection su "dove dovrei investire i miei risparmi?").
- Frontend: `tsc --noEmit`, `next lint`, `next build` senza errori; dashboard e home page
  verificate via richieste HTTP dirette al dev server (`next dev`) dopo un fix a un bug reale
  (`use()` su `params` non è supportato in Next 14 — i `params` della route sono già
  sincroni).
- CORS backend↔frontend verificato con una richiesta preflight `OPTIONS`.
- **Non verificato**: interazione reale in un browser (drag&drop, click, rendering dei
  grafici) — nessuno strumento di automazione browser era disponibile in questo ambiente.
  I dati restituiti dall'API sono stati validati manualmente e i componenti sono tipizzati
  e collegati correttamente, ma resta da fare un giro manuale in Chrome prima della demo.

## Semplificazioni note rispetto a PLAN.md

- **Chat del coach non in streaming**: `POST /api/coach/{id}` ritorna la risposta completa
  in JSON invece di uno stream SSE token-per-token. Funzionalmente equivalente, più semplice
  da testare; lo streaming si può aggiungere in un secondo momento senza cambiare il
  contratto lato frontend (basterebbe cambiare `sendCoachMessage` per leggere uno stream).
- **DocumentParser/Categorizer/DataAnalyzer sono deterministici by design**: usano Claude
  solo come fallback (fallback LLM per PDF non tabellari o descrizioni ambigue). Questo è
  intenzionale, non un compromesso: rende la pipeline testabile e utilizzabile anche senza
  `ANTHROPIC_API_KEY`, e riduce costo/latenza per i casi comuni.

## Deployment

Come da `docs/adr/0004-deploy-railway-vercel.md`:

- **Backend** (FastAPI) → Railway. Variabili: `ANTHROPIC_API_KEY`,
  `DATABASE_PATH` (volume persistente), `FRONTEND_URL`.
- **Frontend** (Next.js) → Vercel, root directory `app/frontend`. Variabile:
  `NEXT_PUBLIC_API_URL`.

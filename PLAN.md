# Piano: Hackathon Tema 02 — Inclusione Finanziaria

## Context

L'obiettivo è realizzare una soluzione per il tema "Inclusione Finanziaria" dell'Hagenthon Accenture Application Engineering. Il problema specifico: una famiglia italiana non riesce a capire dove vanno i propri soldi ogni mese — non identifica le spese "invisibili" (abbonamenti, commissioni) e non ha un quadro chiaro del trend nel tempo. La soluzione analizza gli estratti conto bancari, categorizza le transazioni, visualizza i dati aggregati e affianca l'utente con un assistente educativo (NON consulente finanziario) che confronta i pattern di spesa con benchmark ISTAT e propone opzioni generiche di miglioramento.

Vincolo critico: vietato fornire raccomandazioni di investimento o consulenza personalizzata.

---

## Architettura generale

```
Telegram Bot (aiogram)                Next.js Frontend (Vercel)
        |                                      |
        |--- HTTP POST /api/analyze ----------->|
        |                                      |
        +---------> FastAPI Backend (Railway) <-+
                          |
                    SQLite (aiosqlite)
                          |
              Agent Pipeline (Claude API)
         ┌────────────────────────────────────┐
         │ 1. DocumentParser  (Haiku)         │
         │ 2. Categorizer     (Haiku)         │
         │ 3. DataAnalyzer    (Sonnet)        │
         │ 4. InsightGenerator(Sonnet)        │
         │ 5. EducationalCoach(Sonnet)        │
         └────────────────────────────────────┘
```

Il bot Telegram e la web app condividono lo stesso backend FastAPI. Ogni sessione di analisi viene identificata da un `session_id` UUID salvato in SQLite. Il bot invia all'utente il link `https://<railway-url>/dashboard/{session_id}` dopo l'elaborazione. Il coaching conversazionale funziona su entrambi i canali (web chat + Telegram) chiamando lo stesso Agent 5.

---

## Struttura directory

```
hackaton-ai/
├── .claude/
│   └── settings.json              # Claude Code hooks (lint, test, progress)
├── agents/
│   ├── orchestrator.py            # Pipeline runner: chiama agenti in sequenza
│   ├── document_parser.py         # Agent 1
│   ├── categorizer.py             # Agent 2
│   ├── data_analyzer.py           # Agent 3
│   ├── insight_generator.py       # Agent 4
│   └── educational_coach.py       # Agent 5
├── app/
│   ├── backend/
│   │   ├── main.py                # FastAPI app, SSE endpoint, CORS
│   │   ├── database.py            # SQLite schema + aiosqlite helpers
│   │   ├── models.py              # Pydantic models (Transaction, Session, Insight)
│   │   ├── routes/
│   │   │   ├── upload.py          # POST /api/analyze (multi-file upload)
│   │   │   ├── session.py         # GET /api/session/{id}
│   │   │   └── coach.py           # POST /api/coach/{id} (streaming chat)
│   │   └── telegram_bot.py        # aiogram bot (polling)
│   └── frontend/
│       ├── src/app/
│       │   ├── page.tsx           # Home: file upload
│       │   └── dashboard/[id]/
│       │       └── page.tsx       # Dashboard per session_id
│       └── src/components/
│           ├── FileUpload.tsx
│           ├── AgentProgress.tsx  # SSE progress bar degli agenti
│           ├── charts/
│           │   ├── DonutChart.tsx
│           │   ├── GroupedBarChart.tsx
│           │   ├── LineChart.tsx
│           │   ├── HeatmapCalendar.tsx
│           │   └── SavingsMeter.tsx
│           ├── TopMerchantsTable.tsx
│           └── CoachChat.tsx      # Chat streaming con EducationalCoach
├── data/
│   ├── sample/
│   │   ├── estratto_gennaio_2025.csv
│   │   ├── estratto_febbraio_2025.csv
│   │   └── estratto_marzo_2025.csv
│   ├── istat_benchmarks.json      # % spesa media famiglie italiane ISTAT 2023
│   └── categories.json            # Mapping keyword → categoria
├── requirements.txt
└── README.md
```

---

## Pipeline agentica (dettaglio)

### Agent 1 — DocumentParser (claude-haiku-4-5-20251001)
- **Input**: file bytes (CSV o PDF), filename
- **Tool**: `parse_csv(content)` / `parse_pdf_with_pdfplumber(bytes)`
- **Output**: lista di `Transaction(date, description, amount, type: "entrata"|"uscita")`
- Formato CSV target: stile Intesa Sanpaolo (colonne: Data, Descrizione, Importo, Valuta)
- Auto-detection formato da estensione + header

### Agent 2 — Categorizer (claude-haiku-4-5-20251001)
- **Input**: lista Transaction
- **Tool**: `classify_transaction(description, amount)` → categoria
- **Output**: lista Transaction arricchita con `category`
- Categorie: Alimentari, Ristorazione, Trasporti, Utenze, Abbigliamento, Intrattenimento, Salute, Shopping Online, Commissioni Bancarie, Stipendio/Entrate, Altro
- Usa `categories.json` come lookup veloce + LLM per i casi ambigui

### Agent 3 — DataAnalyzer (claude-sonnet-4-5)
- **Input**: transazioni categorizzate di N mesi
- **Tool**: `compute_aggregates(transactions)` → aggregati per categoria/mese/merchant
- **Output**:
  - Spesa totale per categoria (mese corrente + trend YoY/MoM)
  - Top 10 merchant per importo
  - Entrate vs uscite per mese (line chart data)
  - Heatmap dati (spesa per giorno della settimana)
  - `savings_potential`: delta tra spesa categorie discrezionali e benchmark ISTAT
- Carica `istat_benchmarks.json` per confronto

### Agent 4 — InsightGenerator (claude-sonnet-4-5)
- **Input**: output DataAnalyzer
- **Output**: lista strutturata di 5-7 insight (JSON), es.:
  ```json
  {"category": "Ristorazione", "user_pct": 18, "istat_pct": 8, "trend": "+3%", "severity": "high"}
  ```

### Agent 5 — EducationalCoach (claude-sonnet-4-5)
- **Input**: insight strutturati + domanda utente (per la chat)
- **Comportamento**: spiega i pattern in linguaggio semplice, confronta con benchmark ISTAT, propone 2-3 opzioni generiche non prescrittive (es. "alcune famiglie trovano utile X")
- **MAI**: "dovresti investire", "vendi X", "compra Y", consigli personalizzati
- Mantiene conversation history per la sessione (sia web che Telegram)

### Orchestrator
```python
async def run_pipeline(files, session_id):
    # yield SSE events: "parsing", "categorizing", "analyzing", "generating_insights", "coaching_ready"
    transactions = await document_parser.run(files)
    categorized = await categorizer.run(transactions)
    analysis = await data_analyzer.run(categorized)
    insights = await insight_generator.run(analysis)
    coach_intro = await educational_coach.run(insights)
    await db.save_session(session_id, categorized, analysis, insights, coach_intro)
```

---

## Telegram Bot

```python
# telegram_bot.py (aiogram, polling mode)
@dp.message(F.document)
async def handle_file(message: Message):
    session_id = str(uuid.uuid4())
    # download file → POST to internal /api/analyze
    # await pipeline completion via internal call
    await message.reply(f"✅ Analisi completata!\n🔗 {RAILWAY_URL}/dashboard/{session_id}")

@dp.message(F.text)
async def handle_text(message: Message):
    # route to EducationalCoach con session_id dell'ultimo file caricato dall'utente
    response = await educational_coach.chat(telegram_user_sessions[message.from_user.id], message.text)
    await message.reply(response)
```

---

## Claude Code hooks — `.claude/settings.json`

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{"type": "command", "command": "cd app/backend && ruff check . --fix && ruff format . --quiet 2>/dev/null || true"}]
    }],
    "PreCommit": [{
      "type": "command",
      "command": "cd app/backend && python -m pytest tests/ -q --tb=short 2>/dev/null || true"
    }],
    "Stop": [{
      "type": "command",
      "command": "echo '## '$(date '+%Y-%m-%d %H:%M')' - Task completed' >> PROGRESS.md"
    }]
  }
}
```

---

## Dati di riferimento

### `istat_benchmarks.json` (ISTAT 2023 — famiglie italiane)
```json
{
  "Alimentari": 19.2,
  "Abitazione e Utenze": 34.8,
  "Trasporti": 13.1,
  "Ristorazione": 8.3,
  "Abbigliamento": 6.1,
  "Intrattenimento": 5.8,
  "Salute": 4.2,
  "Shopping Online": 3.9,
  "Altro": 4.6
}
```

### Sample CSV format (stile Intesa Sanpaolo)
```csv
Data,Descrizione,Importo,Valuta
15/01/2025,CONAD SUPERMERCATI,-85.40,EUR
15/01/2025,STIPENDIO ACCENTURE,+2800.00,EUR
16/01/2025,NETFLIX ABBONAMENTO,-17.99,EUR
```

---

## Deployment

- **Backend (FastAPI + Telegram bot)**: Railway — deploy da GitHub, `requirements.txt` auto-detected
- **Frontend (Next.js)**: Vercel — deploy da GitHub, `app/frontend` come root directory
- **Variabili d'ambiente**: `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, `FRONTEND_URL`

---

## Tech Stack

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.12, FastAPI, aiosqlite |
| PDF parsing | pdfplumber |
| AI | Anthropic SDK (claude-haiku-4-5, claude-sonnet-4-5) |
| Telegram | aiogram 3.x |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Charts | Recharts |
| Deploy backend | Railway |
| Deploy frontend | Vercel |

---

## Deliverable hackathon

1. **User Difficulty Statement**: Famiglia italiana (2 adulti, reddito medio) che a fine mese non sa dove sono andati i soldi. Non distingue spese fisse da variabili, non si accorge degli abbonamenti accumulati, non ha mai confrontato la propria spesa con una media di riferimento.

2. **Before/After Simplicity Evidence**: Prima = estratto conto tabellare grezzo con 80 righe di descrizioni bancarie criptiche. Dopo = dashboard con donut chart categorizzato, trend 3 mesi, savings meter che mostra "potresti risparmiare X€/mese portando la ristorazione in linea con la media italiana".

3. **Risk & Clarity Note**: I benchmark usati sono ISTAT pubblici (non personalizzati). Il coach propone opzioni generiche ("alcune famiglie..."), mai prescrizioni. Le semplificazioni non alterano gli importi originali (tutti verificabili nel tab "transazioni dettaglio").

---

## Verifiche end-to-end

1. `cd app/backend && uvicorn main:app --reload` → upload `data/sample/*.csv` via UI → verifica SSE progress → verifica dashboard con tutti i grafici
2. Avvia bot Telegram: `python telegram_bot.py` → manda un CSV al bot → ricevi link Railway → apri dashboard → chatta con il coach
3. Upload di 3 mesi di CSV → verifica che il grouped bar chart mostri il trend corretto
4. Carica un PDF fittizio → verifica che pdfplumber lo parsi correttamente
5. Verifica che il coach NON risponda a "dove dovrei investire i miei risparmi?" con consigli finanziari

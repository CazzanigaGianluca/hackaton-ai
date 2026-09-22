# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
python -m pytest

# Run a single test file
python -m pytest app/backend/agents/tests/test_categorizer.py -v

# Run a single test by name
python -m pytest app/backend/agents/tests/test_categorizer.py::test_classify_by_keyword_matches_known_merchant -v

# Lint and format
ruff check . --fix
ruff format .

# Start the backend (from repo root)
uvicorn app.backend.main:app --reload

# Start the frontend (from app/frontend/)
npm run dev
```

## Architecture

This is an AI-powered personal finance app (Inclusione Finanziaria) that analyzes Italian bank statements and explains spending patterns through an educational assistant — never a financial advisor.

### Request flow

1. User uploads one or more Estratti Conto (CSV or PDF) via `POST /api/analyze`
2. The route creates a SQLite **Sessione** and streams SSE progress events back to the frontend
3. **Orchestrator** (`app/backend/agents/orchestrator.py`) drives 5 agents in sequence:
   - **DocumentParser** → extracts Transazioni from raw files
   - **Categorizer** → assigns a Categoria to each Transazione (keyword lookup first, LLM fallback)
   - **DataAnalyzer** → computes Pattern di Spesa statistics (pure Python, no LLM)
   - **InsightGenerator** → produces Insight structs with severity and ISTAT comparison
   - **EducationalCoach** → generates the opening narrative for the dashboard
4. Final result is persisted to SQLite; frontend polls `GET /api/session/{id}`
5. Chat turns hit `POST /api/coach/{id}` — history is stored in `conversation_json` on the Sessione row

### LLM client abstraction (`app/backend/llm.py`)

`get_llm_client()` returns one of three things:
- `AsyncAnthropic` (SDK) when `ANTHROPIC_API_KEY` is set
- `ClaudeCliClient` (subprocess wrapper for `claude -p`) when the CLI is installed
- `None` when neither is available — all agents must handle this with a deterministic fallback

Every agent receives `llm_client` via constructor injection and must work correctly when it is `None`.

### Agent pattern (mandatory)

```python
class FooAgent:
    def __init__(self, llm_client=None) -> None:
        self._llm = llm_client

    async def run(self, input: InputType) -> OutputType:
        if self._llm is None:
            return self._deterministic_fallback(input)
        # LLM call
```

### Domain vocabulary

Use terms from `CONTEXT.md` exactly. Key ones: **Transazione** (not "movimento"), **Categoria** (not "tag"), **Sessione** (not "utente"), **Estratto Conto** (not "file"), **Risparmio Potenziale** (not "risparmio consigliato"), **Assistente Educativo** (not "chatbot").

### Persistence

Single SQLite file (`sessions.db`, path overridable via `DATABASE_PATH` env var). `append_conversation_message` uses `BEGIN IMMEDIATE` to avoid lost-update races on the conversation history JSON column.

### Safety constraint

`EducationalCoachAgent` has a deterministic `is_investment_advice_request` guard that fires before any LLM call and returns `DEFLECTION_MESSAGE`. The system prompt is the second line of defense. Never remove or weaken the deterministic guard.

## Testing conventions

- Tests live next to the code they test: `app/backend/agents/tests/`, `app/backend/tests/`
- `pytest-asyncio` is in `auto` mode — async test functions need no decorator
- **LLM is stubbed with inline classes, not `unittest.mock`** (see `test_categorizer.py` for the pattern)
- Backend integration tests use `httpx.AsyncClient` with `ASGITransport` and a temp SQLite DB via `monkeypatch` on `database.DATABASE_PATH`
- One test per behaviour, names follow `test_<what>_when_<condition>()`

## Custom skills

Three project-specific Claude Code skills are in `.claude/skills/`:

| Skill | Invocation | Purpose |
|---|---|---|
| generate | `/generate <description>` | Generates code following project conventions |
| review | `/review [file\|PR]` | Security → correctness → conventions review, report only |
| test | `/test <file>` | Generates tests, runs pytest, iterates up to 3 times |

## Mandatory skill workflow

**ALWAYS** invoke these three skills — in this exact order — whenever you create or modify any feature, agent, route, component, or module:

1. `/generate <description>` — before writing new code, use this skill to generate it following project conventions
2. `/test <file>` — after code is written, generate and run tests for every modified file; iterate until all pass
3. `/review <file>` — after tests pass, run the review skill on every modified file and fix any findings before reporting the task as done

No exception: even a one-line fix requires `/test` and `/review` on the affected file. If you skip any of these three steps, the task is not complete.

---
name: review
description: "Code review a tre livelli di priorità: sicurezza (dati bancari, API key, prompt injection), correttezza (race condition, fallback LLM mancante, edge case), convenzioni (CONTEXT.md, pattern agente, typing). Report only, nessun auto-fix."
argument-hint: "[file|path|PR-number]"
---

# review

Esegue code review sul codice indicato con tre livelli di priorità: sicurezza, correttezza, convenzioni.

## 1. Raccogli il codice da revisionare

- **Senza argomenti**: `git diff --cached` + `git diff HEAD` per includere tutto il lavoro non ancora committato
- **Con file/path**: leggi il file o i file nel path
- **Con numero PR**: usa `gh pr diff <numero>`

## 2. Leggi il contesto

Leggi `CONTEXT.md` per avere i termini di dominio corretti prima di giudicare naming e semantica.

## 3. Analizza in tre passate, in ordine di priorità

**PRIORITÀ 1 — Sicurezza** (blocco: va fixato prima di mergiare)
- Dati bancari (importi, descrizioni Transazioni, IBAN) in log, print, o eccezioni
- `ANTHROPIC_API_KEY` o altri segreti esposti in output o stringhe
- Prompt injection: input utente concatenato direttamente in prompt LLM senza sanitizzazione
- Path traversal su upload file (Estratto Conto)
- SQL injection su query SQLite con f-string

**PRIORITÀ 2 — Correttezza** (importante: può causare bug in produzione)
- Race condition in coroutine async (stato condiviso mutabile)
- Fallback mancante quando `llm_client is None` negli agenti
- Gestione errori assente su chiamate LLM (può sollevare `RuntimeError`)
- Logica di calcolo Risparmio Potenziale o Benchmark ISTAT scorretta
- Edge case non gestiti (lista vuota, PDF malformato, Sessione scaduta)

**PRIORITÀ 3 — Convenzioni** (miglioramento: non blocca il merge)
- Termini non aderenti al glossario di `CONTEXT.md`
- Pattern agente non rispettato (manca `llm_client=None`, manca fallback, manca typing)
- `from __future__ import annotations` mancante
- Commenti che spiegano il "cosa" invece del "perché"

## 4. Riporta i risultati

Formato output per ogni trovaglia:

```
[P1|P2|P3] file.py:riga — <descrizione concisa del problema>
           Scenario: <input/stato che causa il problema>
           Suggerimento: <come fixarlo>
```

- Ordina per priorità (P1 prima)
- Se non ci sono trovaglie in una categoria, scrivi "Nessun problema P1/P2/P3 rilevato"
- Non applicare fix automaticamente: il report è il prodotto finale di questa skill

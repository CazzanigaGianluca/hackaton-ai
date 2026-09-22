# ADR 0001 - Orchestrazione agenti con Claude API nativa (no LangGraph/CrewAI)

## Stato

Accepted

## Contesto

Il sistema richiede una pipeline di 5 agenti specializzati (DocumentParser, Categorizer, DataAnalyzer, InsightGenerator, EducationalCoach). Era necessario scegliere come orchestrarli. Le alternative principali erano:

- **LangGraph**: grafo di stati esplicito, ottimo per pipeline con branching complesso
- **CrewAI**: astrazione alta con ruoli, rapido da prototipare
- **Claude API nativa + Python custom**: chiamate dirette all'SDK Anthropic, orchestrazione con codice Python

## Decisione

Usiamo la Claude API nativa con tool use, orchestrata da codice Python custom senza framework di terze parti.

## Motivazione

- **5 ore di sviluppo**: LangGraph richiede circa 1 ora solo di setup e comprensione del modello a grafo. CrewAI aggiunge concetti propri (Crew, Task, Process) che si sovrappongono alla pipeline gia' definita.
- **Debuggabilita'**: in un hackathon, ogni layer di astrazione e' un potenziale punto di failure opaco. Con Python custom ogni chiamata e' tracciabile direttamente.
- **Demo**: poter mostrare il codice degli agenti senza dipendenze magiche e' piu' convincente per i giudici tecnici.
- **La pipeline e' lineare**: non c'e' branching complesso che giustifichi un grafo di stati. Una sequenza `async` Python e' sufficiente.

## Conseguenze

- Ogni agente e' un modulo Python autonomo con la propria system prompt e i propri tools.
- L'orchestratore (`agents/orchestrator.py`) chiama gli agenti in sequenza e gestisce il passaggio di stato.
- Se in futuro il grafo di esecuzione diventasse complesso (branching, retry, parallel), migrare a LangGraph richiederebbe un refactor significativo.

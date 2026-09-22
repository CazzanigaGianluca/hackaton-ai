# ADR 0002 - SQLite come storage persistente delle Sessioni

## Stato

Accepted

## Contesto

I dati di una Sessione (Transazioni categorizzate, Pattern di Spesa, Insight, storia della conversazione) devono essere accessibili sia dalla web app che dal bot Telegram. Era necessario scegliere dove conservarli:

- **In-memory** (dict Python per sessione HTTP): zero setup, ma i dati muoiono al riavvio e non sono condivisibili tra processi
- **Redis**: condivisione tra processi, TTL nativo, richiede un servizio separato
- **SQLite** (aiosqlite): file locale, zero servizi esterni, query SQL per i trend multi-mese, condivisibile tra tutti i processi che puntano allo stesso file

## Decisione

Usiamo SQLite con aiosqlite come unico storage persistente.

## Motivazione

- **Cross-canale**: il bot Telegram e il backend FastAPI girano nello stesso processo (o almeno sullo stesso host Railway). SQLite e' accessibile da entrambi senza un servizio di coordinamento.
- **Trend storici**: le query sui Pattern di Spesa multi-mese sono naturali in SQL (`GROUP BY category, month`). Con strutture in-memory richiederebbero codice custom equivalente.
- **Link Sessione**: il flusso Telegram → link web richiede che la Sessione sopravviva alla risposta HTTP. In-memory non lo garantisce.
- **Zero dipendenze esterne**: non aggiunge complessita' al deploy Railway.

## Conseguenze

- Il file SQLite e' locale al container Railway. Un riavvio del container non perde i dati solo se il volume e' persistente (da configurare su Railway).
- Non e' adatto a scenari multi-istanza (load balancing). Per un hackathon su singola istanza e' sufficiente.
- La migrazione a PostgreSQL in futuro richiede solo di cambiare il driver (aiosqlite → asyncpg) con minime modifiche alle query.

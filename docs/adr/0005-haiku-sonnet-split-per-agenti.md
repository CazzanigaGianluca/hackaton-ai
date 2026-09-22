# ADR 0005 - Modelli Claude differenziati per agente (Haiku vs Sonnet)

## Stato

Accepted

## Contesto

La pipeline ha 5 agenti con complessita' cognitiva molto diversa. Usare claude-sonnet-4-5 per tutti garantisce qualita' massima ma aumenta latenza e costo. Le opzioni valutate:

- **Sonnet per tutti**: massima qualita', latenza ~8-12s per pipeline completa
- **Haiku per tutti**: velocissimo, ma qualita' insufficiente per narrativa educativa complessa
- **Split Haiku/Sonnet**: Haiku per task strutturati (parsing, classificazione), Sonnet per task narrativi e analitici

## Decisione

- `claude-haiku-4-5-20251001`: DocumentParser, Categorizer
- `claude-sonnet-4-5`: DataAnalyzer, InsightGenerator, EducationalCoach

## Motivazione

- **DocumentParser**: estrae dati strutturati da testo semi-strutturato. Output e' JSON con campi fissi. Haiku e' sufficiente e 3-4x piu' veloce.
- **Categorizer**: classificazione a etichetta chiusa (11 categorie) su descrizioni bancarie brevi. Task di classificazione puro, Haiku eccelle.
- **DataAnalyzer**: deve ragionare su trend multi-mese, calcolare delta rispetto a benchmark ISTAT, identificare anomalie. Richiede ragionamento quantitativo: Sonnet.
- **InsightGenerator**: deve produrre insight strutturati con severita' e contesto. Richiede comprensione del significato, non solo estrazione: Sonnet.
- **EducationalCoach**: produce narrativa educativa in italiano, deve essere chiaro, empatico e non prescrittivo. Qualita' linguistica critica: Sonnet obbligatorio.

## Conseguenze

- La latenza della pipeline e' dominata dagli agenti Sonnet (3-4). Haiku per i primi 2 agenti riduce il tempo totale di circa 1.5-2 secondi.
- Il costo per analisi e' ridotto di circa 30-40% rispetto a Sonnet per tutti.
- Se Haiku produce categorizzazioni errate su descrizioni bancarie ambigue, il fallback e' promuovere Categorizer a Sonnet (modifica a una riga in `categorizer.py`).

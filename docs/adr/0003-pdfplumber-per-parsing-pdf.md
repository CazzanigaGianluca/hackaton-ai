# ADR 0003 - pdfplumber per il parsing dei PDF bancari

## Stato

Accepted

## Contesto

Gli Estratti Conto in formato PDF devono essere convertiti in lista di Transazioni strutturate. Le alternative erano:

- **pdfplumber**: libreria Python specializzata nell'estrazione di tabelle da PDF, API pythonica
- **PyMuPDF (fitz)**: piu' veloce, estrae testo raw, richiede post-processing manuale per le tabelle
- **Claude Vision**: invia il PDF come immagine a Claude che estrae le Transazioni direttamente, zero librerie di parsing

## Decisione

Usiamo pdfplumber per il parsing dei PDF.

## Motivazione

- **Determinismo**: pdfplumber produce output deterministico a partire dallo stesso PDF. Claude Vision puo' variare tra chiamate e aggiunge latenza e costo per ogni pagina del documento.
- **Costo**: Claude Vision per un PDF di 3 pagine costa circa 10-15x piu' di pdfplumber (che e' gratuito e locale).
- **Formato target noto**: il formato dei PDF degli estratti conto Intesa Sanpaolo/Fineco e' strutturato con tabelle regolari, scenario in cui pdfplumber eccelle.
- **Fallback**: se pdfplumber non riesce a estrarre le tabelle (PDF scansionati, layout non standard), e' possibile aggiungere Claude Vision come fallback in un secondo momento senza cambiare l'interfaccia dell'agente.

## Conseguenze

- Il parser e' ottimizzato per il formato Intesa Sanpaolo/Fineco incluso come sample. PDF di altri istituti potrebbero richiedere adattamenti alle regole di estrazione delle colonne.
- PDF scansionati (immagini) non sono supportati nella versione iniziale.

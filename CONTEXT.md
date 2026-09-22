# Inclusione Finanziaria - Glossario di dominio

## Termini

**Estratto Conto**
Documento bancario emesso periodicamente (mensile) che elenca tutti i movimenti di un conto corrente in un intervallo di tempo. E' la sorgente dati primaria del sistema. Puo' essere in formato CSV o PDF.
_Evita_: "file bancario", "documento", "export"

**Transazione**
Singolo movimento registrato in un Estratto Conto. Ha sempre: data, descrizione (testo libero della banca), importo (positivo o negativo), tipo (Entrata o Uscita).
_Evita_: "movimento", "riga", "operazione"

**Entrata**
Transazione con importo positivo: stipendio, rimborsi, bonifici ricevuti, accrediti.
_Evita_: "credito" (termine bancario ambiguo)

**Uscita**
Transazione con importo negativo: acquisti, pagamenti, prelievi, commissioni.
_Evita_: "debito" (termine bancario ambiguo)

**Categoria**
Classificazione semantica assegnata a ogni Transazione. Insieme chiuso di valori: Alimentari, Ristorazione, Trasporti, Utenze, Abbigliamento, Intrattenimento, Salute, Shopping Online, Commissioni Bancarie, Stipendio/Entrate, Altro.
_Evita_: "tag", "label", "tipo spesa"

**Pattern di Spesa**
Aggregazione statistica delle Transazioni di una Sessione su una o piu' dimensioni (Categoria, merchant, mese, giorno della settimana). Non e' un singolo dato ma una vista aggregata.
_Evita_: "analisi", "report", "summary"

**Benchmark ISTAT**
Percentuali di spesa media delle famiglie italiane per Categoria, derivate dai dati ISTAT 2023. Usato esclusivamente come riferimento educativo comparativo, mai come target prescrittivo.
_Evita_: "media italiana", "standard", "obiettivo"

**Risparmio Potenziale**
Delta calcolato tra la spesa effettiva dell'utente in categorie discrezionali (Ristorazione, Intrattenimento, Shopping Online) e il corrispondente Benchmark ISTAT applicato al reddito osservato. E' un indicatore educativo, non una raccomandazione.
_Evita_: "risparmio consigliato", "obiettivo di risparmio"

**Sessione**
Unita' di lavoro identificata da un UUID. Raggruppa tutti gli Estratti Conto caricati in un singolo upload (uno o piu' mesi), le Transazioni estratte, i Patterns di Spesa calcolati e la storia della conversazione con l'Assistente Educativo. Persiste in SQLite.
_Evita_: "utente", "profilo", "account"

**Assistente Educativo**
Componente AI (Agent 5 - EducationalCoach) che spiega i Pattern di Spesa in linguaggio semplice, confronta con i Benchmark ISTAT e propone opzioni generiche non prescrittive. Non e' un consulente finanziario: non da' raccomandazioni di investimento ne' consigli personalizzati.
_Evita_: "consulente", "advisor", "chatbot"

**Insight**
Osservazione strutturata generata da InsightGenerator su un Pattern di Spesa specifico. Ha: categoria, percentuale utente, percentuale ISTAT, trend rispetto ai mesi precedenti, severita' (low/medium/high). E' l'input strutturato che l'Assistente Educativo trasforma in narrativa.
_Evita_: "alert", "suggerimento", "consiglio"

## Relazioni

- Una Sessione contiene uno o piu' Estratti Conto (mesi diversi)
- Un Estratto Conto contiene molte Transazioni
- Ogni Transazione appartiene a esattamente una Categoria
- Una Sessione produce un insieme di Pattern di Spesa
- I Pattern di Spesa generano Insight (tramite InsightGenerator)
- L'Assistente Educativo narra gli Insight all'utente

## Ambiguita' risolte

- "risparmio" era ambiguo tra "denaro messo da parte" e "riduzione della spesa". Risolto: nel sistema Risparmio Potenziale indica esclusivamente la riduzione possibile della spesa discrezionale, non un accantonamento.
- "utente" era usato sia per la persona fisica che per la sessione tecnica. Risolto: la persona e' sempre "utente" nel discorso UX; il costrutto tecnico che la rappresenta e' sempre "Sessione".

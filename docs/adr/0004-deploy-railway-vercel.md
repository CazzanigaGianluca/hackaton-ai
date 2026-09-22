# ADR 0004 - Deploy su Railway (backend) + Vercel (frontend)

## Stato

Accepted

## Contesto

La soluzione deve essere raggiungibile pubblicamente per due motivi: il bot Telegram riceve webhook da Telegram (necessita URL pubblico) e il link che il bot invia all'utente deve essere apribile da browser. Le opzioni valutate:

- **ngrok / localtunnel / cloudflare tunnel**: tunnel locali gratuiti, bloccati dalla rete aziendale dell'hackathon
- **Railway (backend) + Vercel (frontend)**: deploy da GitHub, URL stabili, free tier sufficiente
- **Single platform (Railway o Render per tutto)**: piu' semplice ma meno ottimizzato (Next.js su Railway non ha l'edge network di Vercel)

## Decisione

Backend FastAPI (incluso bot Telegram) su Railway. Frontend Next.js su Vercel.

## Motivazione

- **Rete aziendale blocca i tunnel**: ngrok, cloudflare tunnel e localtunnel sono tutti bloccati. Serve un URL pubblico reale.
- **Vercel e' ottimale per Next.js**: deploy automatico da GitHub in meno di 5 minuti, CDN globale, zero configurazione per Next.js.
- **Railway gestisce Python + SQLite**: supporta `requirements.txt` nativo, processi multipli (FastAPI + bot Telegram), e volumi persistenti per SQLite.
- **Free tier sufficiente**: per un hackathon di 5 ore entrambi i free tier sono ampiamente sufficienti.

## Conseguenze

- Il frontend deve avere la variabile `NEXT_PUBLIC_API_URL` puntata all'URL Railway.
- Il backend deve avere `FRONTEND_URL` puntato all'URL Vercel per costruire i link corretti nei messaggi Telegram.
- Il bot Telegram usa polling (non webhook) per evitare la necessita' di configurare SSL e registrare l'URL del webhook su Telegram durante il setup iniziale.

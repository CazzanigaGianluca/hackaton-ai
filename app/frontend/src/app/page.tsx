import FileUpload from "@/components/FileUpload";

export default function Home() {
  return (
    <main className="flex min-h-[calc(100dvh-3.5rem)] flex-col items-center justify-center gap-12 px-4 py-16">
      {/* Hero */}
      <div className="max-w-lg text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--primary)] shadow-lg shadow-blue-900/20">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="5" width="20" height="14" rx="2"/>
            <line x1="2" y1="10" x2="22" y2="10"/>
          </svg>
        </div>
        <h1 className="text-3xl font-bold leading-tight text-[var(--text)] text-balance">
          Dove vanno i tuoi soldi ogni mese?
        </h1>
        <p className="mt-4 text-[var(--text-secondary)] text-balance leading-relaxed">
          Carica il tuo Estratto Conto (CSV o PDF). Analizziamo le tue spese, le confrontiamo
          con la media ISTAT e ti aiutiamo a capire i tuoi pattern di consumo — senza consigli
          di investimento, solo educazione finanziaria.
        </p>
        <div className="mt-6 flex justify-center gap-4 text-xs text-[var(--text-muted)]">
          <span className="flex items-center gap-1.5">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            CSV e PDF
          </span>
          <span className="flex items-center gap-1.5">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            Dati sicuri e privati
          </span>
          <span className="flex items-center gap-1.5">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            Confronto ISTAT
          </span>
        </div>
      </div>

      <FileUpload />

      {/* Footer disclaimer */}
      <p className="max-w-sm text-center text-xs text-[var(--text-muted)]">
        Questo strumento fornisce esclusivamente educazione finanziaria. Non costituisce consulenza
        di investimento ai sensi del D.Lgs. 58/1998.
      </p>
    </main>
  );
}

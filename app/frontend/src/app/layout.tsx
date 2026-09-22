import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Inclusione Finanziaria",
  description: "Capisci dove vanno i tuoi soldi ogni mese",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="it">
      <body className="antialiased">
        <nav className="sticky top-0 z-40 border-b border-[var(--border)] bg-white/90 backdrop-blur-sm">
          <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
            <a href="/" className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--primary)]">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <span className="text-sm font-semibold text-[var(--text)]">Inclusione Finanziaria</span>
            </a>
            <span className="rounded-full bg-[var(--primary-light)] px-3 py-1 text-xs font-medium text-[var(--primary)]">
              Solo educazione finanziaria
            </span>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}

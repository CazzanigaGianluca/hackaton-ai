"use client";

import { useEffect, useState } from "react";
import { getSession } from "@/lib/api";
import { PIPELINE_STAGE_LABELS, SessionData, Severity } from "@/lib/types";
import DonutChart from "@/components/charts/DonutChart";
import GroupedBarChart from "@/components/charts/GroupedBarChart";
import LineChart from "@/components/charts/LineChart";
import HeatmapCalendar from "@/components/charts/HeatmapCalendar";
import SavingsMeter from "@/components/charts/SavingsMeter";
import TopMerchantsTable from "@/components/TopMerchantsTable";
import FloatingChat from "@/components/FloatingChat";

const SEVERITY_CONFIG: Record<Severity, { bg: string; border: string; text: string; icon: string }> = {
  high: { bg: "var(--danger-light)", border: "var(--danger)", text: "var(--danger)", icon: "↑" },
  medium: { bg: "var(--warning-light)", border: "var(--warning)", text: "var(--warning)", icon: "→" },
  low: { bg: "var(--bg)", border: "var(--border)", text: "var(--text-secondary)", icon: "↓" },
};

function StatCard({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent?: boolean }) {
  return (
    <div className={`rounded-2xl border p-4 ${accent ? "border-[var(--primary)] bg-[var(--primary-light)]" : "border-[var(--border)] bg-white"}`} style={{ boxShadow: "var(--shadow-sm)" }}>
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${accent ? "text-[var(--primary)]" : "text-[var(--text)]"}`}>{value}</p>
      {sub && <p className="mt-0.5 text-xs text-[var(--text-muted)]">{sub}</p>}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-white p-5" style={{ boxShadow: "var(--shadow-sm)" }}>
      <h2 className="mb-4 text-sm font-semibold text-[var(--text)]">{title}</h2>
      {children}
    </div>
  );
}

export default function DashboardPage({ params }: { params: { id: string } }) {
  const { id: sessionId } = params;
  const [session, setSession] = useState<SessionData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;

    const poll = () => {
      getSession(sessionId)
        .then((data) => {
          if (cancelled) return;
          setSession(data);
          if (data.status !== "coaching_ready" && data.status !== "failed") {
            timeoutId = setTimeout(poll, 2000);
          }
        })
        .catch((err) => {
          if (!cancelled) setError(err instanceof Error ? err.message : "Errore");
        });
    };

    poll();
    return () => { cancelled = true; clearTimeout(timeoutId); };
  }, [sessionId]);

  if (error) {
    return (
      <main className="flex min-h-[calc(100dvh-3.5rem)] items-center justify-center px-4">
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--danger-light)]">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <p className="font-semibold text-[var(--text)]">Si è verificato un errore</p>
          <p className="text-sm text-[var(--text-muted)]">{error}</p>
        </div>
      </main>
    );
  }

  if (session?.status === "failed") {
    return (
      <main className="flex min-h-[calc(100dvh-3.5rem)] flex-col items-center justify-center gap-3 px-4 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--danger-light)]">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <p className="font-semibold text-[var(--text)]">Analisi non riuscita</p>
        <p className="text-sm text-[var(--text-muted)]">Verifica che il file sia in formato CSV o PDF supportato e riprova.</p>
        <a href="/" className="mt-2 rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--primary-hover)]">
          Torna alla home
        </a>
      </main>
    );
  }

  if (!session || !session.analysis) {
    return (
      <main className="flex min-h-[calc(100dvh-3.5rem)] flex-col items-center justify-center gap-4 px-4">
        <div className="relative flex h-12 w-12 items-center justify-center">
          <span className="absolute inset-0 animate-ping rounded-full bg-[var(--primary)] opacity-20" />
          <span className="relative flex h-8 w-8 items-center justify-center rounded-full bg-[var(--primary)]">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </span>
        </div>
        <p className="text-sm font-medium text-[var(--text)]">
          {session
            ? `${PIPELINE_STAGE_LABELS[session.status] ?? session.status}...`
            : "Caricamento della dashboard..."}
        </p>
        <p className="text-xs text-[var(--text-muted)]">Attendere qualche momento</p>
      </main>
    );
  }

  const { analysis, insights, transactions, coach_intro, conversation } = session;

  const totalExpenses = transactions
    .filter((t) => t.type === "uscita")
    .reduce((sum, t) => sum + t.amount, 0);

  const totalIncome = transactions
    .filter((t) => t.type === "entrata")
    .reduce((sum, t) => sum + t.amount, 0);

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      {/* Header */}
      <header className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)]">Dashboard finanziaria</h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            {transactions.length} transazioni analizzate
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 self-start rounded-full border border-[var(--border)] bg-white px-3 py-1.5 text-xs font-medium text-[var(--text-muted)] sm:self-auto">
          <span className="h-1.5 w-1.5 rounded-full bg-[var(--success)]" />
          Analisi completata
        </span>
      </header>

      {/* Stat cards */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Transazioni" value={String(transactions.length)} sub="totali analizzate" />
        <StatCard label="Uscite totali" value={`€${totalExpenses.toFixed(0)}`} sub="nel periodo" />
        <StatCard label="Entrate totali" value={`€${totalIncome.toFixed(0)}`} sub="nel periodo" accent />
        <StatCard label="Categorie" value={String(Object.keys(analysis.by_category).length)} sub="identificate" />
      </section>

      {/* Charts row 1 */}
      <section className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Spesa per categoria">
          <DonutChart byCategory={analysis.by_category} />
        </ChartCard>
        <ChartCard title="Entrate vs uscite nel tempo">
          <LineChart monthlyTotals={analysis.monthly_totals} />
        </ChartCard>
      </section>

      {/* Charts row 2 */}
      <ChartCard title="Trend di spesa per categoria (mese su mese)">
        <GroupedBarChart byCategoryByMonth={analysis.by_category_by_month} />
      </ChartCard>

      {/* Charts row 3 */}
      <section className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Spesa per giorno della settimana">
          <HeatmapCalendar heatmapByWeekday={analysis.heatmap_by_weekday} />
        </ChartCard>
        <ChartCard title="Risparmio potenziale vs media ISTAT">
          <SavingsMeter savingsPotential={analysis.savings_potential} />
        </ChartCard>
      </section>

      {/* Merchants + Insights */}
      <section className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Top 10 merchant">
          <TopMerchantsTable topMerchants={analysis.top_merchants} />
        </ChartCard>

        <div className="rounded-2xl border border-[var(--border)] bg-white p-5" style={{ boxShadow: "var(--shadow-sm)" }}>
          <h2 className="mb-4 text-sm font-semibold text-[var(--text)]">Insight sulle tue spese</h2>
          <ul className="space-y-2">
            {insights.map((insight) => {
              const cfg = SEVERITY_CONFIG[insight.severity];
              return (
                <li
                  key={insight.category}
                  className="flex items-start gap-3 rounded-xl border p-3 text-sm"
                  style={{ background: cfg.bg, borderColor: cfg.border }}
                >
                  <span className="mt-0.5 text-base leading-none" style={{ color: cfg.text }}>{cfg.icon}</span>
                  <div>
                    <p className="font-semibold" style={{ color: cfg.text }}>{insight.category}</p>
                    <p className="text-xs" style={{ color: cfg.text, opacity: 0.8 }}>
                      Tu {insight.user_pct}% · Media ISTAT {insight.istat_pct}% · Trend {insight.trend}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      </section>

      {/* Transaction detail */}
      <details className="group rounded-2xl border border-[var(--border)] bg-white" style={{ boxShadow: "var(--shadow-sm)" }}>
        <summary className="flex cursor-pointer items-center justify-between px-5 py-4 text-sm font-semibold text-[var(--text)] marker:content-['']">
          <span>Transazioni dettaglio</span>
          <svg className="transition-transform group-open:rotate-180" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </summary>
        <div className="overflow-x-auto border-t border-[var(--border)]">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--bg)] text-left text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
                <th className="px-5 py-3">Data</th>
                <th className="px-5 py-3">Descrizione</th>
                <th className="px-5 py-3">Categoria</th>
                <th className="px-5 py-3 text-right">Importo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {transactions.map((t, index) => (
                <tr key={index} className="transition-colors hover:bg-[var(--bg)]">
                  <td className="px-5 py-3 font-mono text-xs text-[var(--text-muted)]">{t.date}</td>
                  <td className="max-w-xs px-5 py-3 text-[var(--text)]">{t.description}</td>
                  <td className="px-5 py-3">
                    <span className="rounded-full bg-[var(--bg)] px-2 py-0.5 text-xs font-medium text-[var(--text-secondary)]">
                      {t.category}
                    </span>
                  </td>
                  <td className={`px-5 py-3 text-right font-semibold tabular-nums ${t.type === "entrata" ? "text-[var(--success)]" : "text-[var(--text)]"}`}>
                    {t.type === "entrata" ? "+" : ""}€{t.amount.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <FloatingChat
        sessionId={sessionId}
        analysis={analysis}
        insights={insights}
        initialConversation={
          conversation.length > 0
            ? conversation
            : coach_intro
              ? [{ role: "assistant", content: coach_intro }]
              : []
        }
      />
    </main>
  );
}

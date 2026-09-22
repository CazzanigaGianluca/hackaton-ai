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
import CoachChat from "@/components/CoachChat";

const SEVERITY_STYLES: Record<Severity, string> = {
  high: "border-red-300 bg-red-50 text-red-800",
  medium: "border-amber-300 bg-amber-50 text-amber-800",
  low: "border-gray-200 bg-gray-50 text-gray-700",
};

export default function DashboardPage({
  params,
}: {
  params: { id: string };
}) {
  const { id: sessionId } = params;
  const [session, setSession] = useState<SessionData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // La Sessione potrebbe non essere ancora pronta (reload della pagina durante
  // l'elaborazione, o link condiviso aperto in anticipo): finche' lo stato non e'
  // 'coaching_ready' o 'failed' continuiamo a interrogare il backend.
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
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [sessionId]);

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-red-600">{error}</p>
      </main>
    );
  }

  if (session?.status === "failed") {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-2 px-4 text-center">
        <p className="text-red-600">
          L&apos;analisi di questo Estratto Conto non è riuscita.
        </p>
        <p className="text-sm text-gray-500">
          Verifica che il file sia in un formato supportato (CSV o PDF) e riprova a
          caricarlo dalla home.
        </p>
      </main>
    );
  }

  if (!session || !session.analysis) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-2">
        <p className="text-gray-500">
          {session
            ? `Sto ancora elaborando i tuoi dati: ${PIPELINE_STAGE_LABELS[session.status] ?? session.status}...`
            : "Caricamento della dashboard..."}
        </p>
      </main>
    );
  }

  const { analysis, insights, transactions, coach_intro, conversation } = session;

  return (
    <main className="mx-auto max-w-6xl space-y-8 px-4 py-10">
      <header>
        <h1 className="text-2xl font-bold text-gray-900">La tua dashboard di spesa</h1>
        <p className="text-sm text-gray-500">
          {transactions.length} transazioni analizzate · dati verificabili nel tab dettaglio
          in fondo alla pagina.
        </p>
      </header>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold text-gray-700">
            Spesa per categoria
          </h2>
          <DonutChart byCategory={analysis.by_category} />
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold text-gray-700">
            Entrate vs uscite nel tempo
          </h2>
          <LineChart monthlyTotals={analysis.monthly_totals} />
        </div>
      </section>

      <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold text-gray-700">
          Trend di spesa per categoria (mese su mese)
        </h2>
        <GroupedBarChart byCategoryByMonth={analysis.by_category_by_month} />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold text-gray-700">
            Spesa per giorno della settimana
          </h2>
          <HeatmapCalendar heatmapByWeekday={analysis.heatmap_by_weekday} />
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold text-gray-700">
            Risparmio potenziale (vs media ISTAT)
          </h2>
          <SavingsMeter savingsPotential={analysis.savings_potential} />
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Top 10 merchant</h2>
          <TopMerchantsTable topMerchants={analysis.top_merchants} />
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Insight</h2>
          <ul className="space-y-2">
            {insights.map((insight) => (
              <li
                key={insight.category}
                className={`rounded-lg border px-3 py-2 text-sm ${SEVERITY_STYLES[insight.severity]}`}
              >
                <span className="font-medium">{insight.category}</span>: tu{" "}
                {insight.user_pct}% vs media ISTAT {insight.istat_pct}% (trend{" "}
                {insight.trend})
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">
          Chiedi all&apos;Assistente Educativo
        </h2>
        <CoachChat
          sessionId={sessionId}
          initialConversation={
            conversation.length > 0
              ? conversation
              : coach_intro
                ? [{ role: "assistant", content: coach_intro }]
                : []
          }
        />
      </section>

      <details className="rounded-xl border border-gray-200 bg-white p-4">
        <summary className="cursor-pointer text-sm font-semibold text-gray-700">
          Transazioni dettaglio (dati originali, non modificati)
        </summary>
        <table className="mt-3 w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-gray-500">
              <th className="py-2">Data</th>
              <th className="py-2">Descrizione</th>
              <th className="py-2">Categoria</th>
              <th className="py-2 text-right">Importo</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((t, index) => (
              <tr key={index} className="border-b border-gray-100">
                <td className="py-2 text-gray-500">{t.date}</td>
                <td className="py-2 text-gray-800">{t.description}</td>
                <td className="py-2 text-gray-500">{t.category}</td>
                <td
                  className={`py-2 text-right font-medium ${
                    t.type === "entrata" ? "text-emerald-600" : "text-gray-800"
                  }`}
                >
                  €{t.amount.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </main>
  );
}

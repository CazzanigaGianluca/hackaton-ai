import { SavingsPotentialEntry } from "@/lib/types";

interface SavingsMeterProps {
  savingsPotential: Record<string, SavingsPotentialEntry>;
}

export default function SavingsMeter({ savingsPotential }: SavingsMeterProps) {
  const entries = Object.entries(savingsPotential).filter(
    ([, v]) => v.delta_eur > 0,
  );

  if (entries.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        Le tue spese discrezionali sono in linea con la media delle famiglie italiane (dati
        ISTAT).
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {entries.map(([category, stats]) => {
        const widthPct = Math.min(100, (stats.istat_pct / stats.user_pct) * 100);
        return (
          <div key={category}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="font-medium text-gray-800">{category}</span>
              <span className="text-gray-500">
                tu: {stats.user_pct}% · media ISTAT: {stats.istat_pct}%
              </span>
            </div>
            <div className="h-3 w-full overflow-hidden rounded-full bg-red-100">
              <div
                className="h-full rounded-full bg-emerald-500"
                style={{ width: `${widthPct}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-gray-600">
              Potresti avere fino a{" "}
              <span className="font-semibold text-emerald-700">
                €{stats.delta_eur.toFixed(0)}/mese
              </span>{" "}
              di margine su {category.toLowerCase()} portando la spesa in linea con la media
              ISTAT.
            </p>
          </div>
        );
      })}
    </div>
  );
}

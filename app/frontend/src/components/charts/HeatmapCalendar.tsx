interface HeatmapCalendarProps {
  heatmapByWeekday: Record<string, number>;
}

const WEEKDAY_ORDER = [
  "Lunedì",
  "Martedì",
  "Mercoledì",
  "Giovedì",
  "Venerdì",
  "Sabato",
  "Domenica",
];

/** Intensita' di spesa per giorno della settimana (aggregata su tutti i mesi). */
export default function HeatmapCalendar({ heatmapByWeekday }: HeatmapCalendarProps) {
  const max = Math.max(...Object.values(heatmapByWeekday), 1);

  return (
    <div className="grid grid-cols-7 gap-2">
      {WEEKDAY_ORDER.map((day) => {
        const value = heatmapByWeekday[day] ?? 0;
        const intensity = value / max;
        return (
          <div key={day} className="flex flex-col items-center gap-1">
            <div
              className="flex h-16 w-full items-center justify-center rounded-md text-xs font-medium text-white"
              style={{
                backgroundColor: `rgba(37, 99, 235, ${0.15 + intensity * 0.85})`,
              }}
              title={`€${value.toFixed(2)}`}
            >
              €{value.toFixed(0)}
            </div>
            <span className="text-xs text-gray-500">{day.slice(0, 3)}</span>
          </div>
        );
      })}
    </div>
  );
}

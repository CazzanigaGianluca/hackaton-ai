"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface GroupedBarChartProps {
  byCategoryByMonth: Record<string, Record<string, number>>;
}

const COLORS = [
  "#2563eb",
  "#16a34a",
  "#f59e0b",
  "#dc2626",
  "#7c3aed",
  "#0891b2",
];

/** Trend mensile per categoria: una barra per mese, raggruppata per categoria. */
export default function GroupedBarChart({ byCategoryByMonth }: GroupedBarChartProps) {
  const categories = Object.keys(byCategoryByMonth);
  const months = Array.from(
    new Set(categories.flatMap((c) => Object.keys(byCategoryByMonth[c]))),
  ).sort();

  if (months.length === 0) {
    return <p className="text-sm text-gray-500">Nessun dato mensile disponibile.</p>;
  }

  const data = months.map((month) => {
    const row: Record<string, number | string> = { month };
    categories.forEach((category) => {
      row[category] = byCategoryByMonth[category][month] ?? 0;
    });
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip formatter={(value: number) => `€${value.toFixed(2)}`} />
        <Legend />
        {categories.map((category, index) => (
          <Bar key={category} dataKey={category} fill={COLORS[index % COLORS.length]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

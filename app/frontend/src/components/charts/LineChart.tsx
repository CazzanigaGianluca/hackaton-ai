"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart as RechartsLineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { MonthlyTotal } from "@/lib/types";

interface LineChartProps {
  monthlyTotals: Record<string, MonthlyTotal>;
}

export default function LineChart({ monthlyTotals }: LineChartProps) {
  const months = Object.keys(monthlyTotals).sort();

  if (months.length === 0) {
    return <p className="text-sm text-gray-500">Nessun dato mensile disponibile.</p>;
  }

  const data = months.map((month) => ({
    month,
    entrate: monthlyTotals[month].entrate,
    uscite: monthlyTotals[month].uscite,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RechartsLineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip formatter={(value: number) => `€${value.toFixed(2)}`} />
        <Legend />
        <Line type="monotone" dataKey="entrate" stroke="#16a34a" strokeWidth={2} />
        <Line type="monotone" dataKey="uscite" stroke="#dc2626" strokeWidth={2} />
      </RechartsLineChart>
    </ResponsiveContainer>
  );
}

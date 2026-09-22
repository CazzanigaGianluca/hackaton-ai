import { TopMerchant } from "@/lib/types";

interface TopMerchantsTableProps {
  topMerchants: TopMerchant[];
}

export default function TopMerchantsTable({ topMerchants }: TopMerchantsTableProps) {
  if (topMerchants.length === 0) {
    return <p className="text-sm text-gray-500">Nessun merchant da mostrare.</p>;
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-200 text-left text-gray-500">
          <th className="py-2">Merchant</th>
          <th className="py-2 text-right">Transazioni</th>
          <th className="py-2 text-right">Totale</th>
        </tr>
      </thead>
      <tbody>
        {topMerchants.map((merchant) => (
          <tr key={merchant.description} className="border-b border-gray-100">
            <td className="py-2 text-gray-800">{merchant.description}</td>
            <td className="py-2 text-right text-gray-500">{merchant.count}</td>
            <td className="py-2 text-right font-medium text-gray-800">
              €{merchant.total.toFixed(2)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

'use client';

import { useState } from 'react';
import { ArrowLeft, Download } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface VarianceReportProps {
  onBack: () => void;
}

export default function VarianceReport({ onBack }: VarianceReportProps) {
  const [selectedStockTake, setSelectedStockTake] = useState<number | ''>('');

  // Fetch stock takes
  const { data: stockTakes } = useQuery({
    queryKey: ['stock-takes'],
    queryFn: async () => {
      const response = await api.get('/api/stock-control/stock-takes/');
      return response.data.results || response.data;
    },
  });

  // Fetch variance items
  const { data: varianceItems, isLoading } = useQuery({
    queryKey: ['variance-items', selectedStockTake],
    queryFn: async () => {
      if (!selectedStockTake) return [];
      const response = await api.get(`/api/stock-control/stock-takes/${selectedStockTake}/items/`);
      const items = response.data.results || response.data;
      return items.filter((item: any) => item.variance_quantity !== 0);
    },
    enabled: !!selectedStockTake,
  });

  const calculateTotals = () => {
    if (!varianceItems) return { quantity: 0, value: 0 };
    return {
      quantity: varianceItems.reduce((sum: number, item: any) => sum + (item.variance_quantity || 0), 0),
      value: varianceItems.reduce((sum: number, item: any) => sum + (item.variance_value || 0), 0),
    };
  };

  const totals = calculateTotals();

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          <ArrowLeft size={20} />
          Back
        </button>
        <h3 className="text-2xl font-bold">Stock Variance Report</h3>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Select Stock Take</label>
        <select
          value={selectedStockTake}
          onChange={(e) => setSelectedStockTake(e.target.value ? parseInt(e.target.value) : '')}
          className="w-full md:w-80 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">-- Select Stock Take --</option>
          {stockTakes?.map((st: any) => (
            <option key={st.id} value={st.id}>
              {st.stock_take_date} ({st.status})
            </option>
          ))}
        </select>
      </div>

      {selectedStockTake && (
        <>
          <div className="overflow-x-auto mb-6">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 border-b">
                <tr>
                  <th className="text-left px-4 py-2">Stock Code</th>
                  <th className="text-left px-4 py-2">Description</th>
                  <th className="text-right px-4 py-2">System Qty</th>
                  <th className="text-right px-4 py-2">Counted Qty</th>
                  <th className="text-right px-4 py-2">Variance Qty</th>
                  <th className="text-right px-4 py-2">Cost Price</th>
                  <th className="text-right px-4 py-2">Variance Value</th>
                </tr>
              </thead>
              <tbody>
                {varianceItems?.map((item: any, index: number) => (
                  <tr key={index} className={`border-b ${item.variance_quantity < 0 ? 'bg-red-50' : 'bg-green-50'}`}>
                    <td className="px-4 py-2 font-medium">{item.stock_item.stock_code}</td>
                    <td className="px-4 py-2">{item.stock_item.description}</td>
                    <td className="text-right px-4 py-2">{item.quantity_on_hand.toFixed(2)}</td>
                    <td className="text-right px-4 py-2">{item.quantity_counted.toFixed(2)}</td>
                    <td className={`text-right px-4 py-2 font-semibold ${item.variance_quantity < 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {item.variance_quantity.toFixed(2)}
                    </td>
                    <td className="text-right px-4 py-2">R {item.cost_price_at_count.toFixed(2)}</td>
                    <td className={`text-right px-4 py-2 font-semibold ${item.variance_value < 0 ? 'text-red-600' : 'text-green-600'}`}>
                      R {item.variance_value.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {varianceItems && varianceItems.length > 0 && (
            <div className="mb-6 space-y-2 text-right max-w-md ml-auto">
              <div className="flex justify-between text-sm border-t pt-2">
                <span>Total Variance Qty:</span>
                <span className={`font-bold ${totals.quantity < 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {totals.quantity.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-lg border-t pt-2">
                <span>Total Variance Value:</span>
                <span className={`font-bold ${totals.value < 0 ? 'text-red-600' : 'text-green-600'}`}>
                  R {totals.value.toFixed(2)}
                </span>
              </div>
            </div>
          )}

          {varianceItems && varianceItems.length === 0 && (
            <div className="p-4 bg-green-50 border-l-4 border-green-600 rounded">
              <p className="text-sm text-green-800">
                <strong>No Variances Found:</strong> All counted quantities match system quantities.
              </p>
            </div>
          )}
        </>
      )}

      <div className="flex gap-4 justify-center">
        <button
          onClick={onBack}
          className="px-6 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition"
        >
          Back
        </button>
        <button
          disabled={!selectedStockTake}
          className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
        >
          <Download size={20} />
          Export Report
        </button>
      </div>
    </div>
  );
}

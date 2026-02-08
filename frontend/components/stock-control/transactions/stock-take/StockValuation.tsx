'use client';

import { useState } from 'react';
import { ArrowLeft, Download } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface StockValuationProps {
  onBack: () => void;
}

export default function StockValuation({ onBack }: StockValuationProps) {
  const [selectedStockTake, setSelectedStockTake] = useState<number | ''>('');
  const [valuationType, setValuationType] = useState('actual');

  // Fetch stock takes
  const { data: stockTakes } = useQuery({
    queryKey: ['stock-takes'],
    queryFn: async () => {
      const response = await api.get('/api/stock-control/stock-takes/');
      return response.data.results || response.data;
    },
  });

  // Fetch valuation items
  const { data: valuationItems } = useQuery({
    queryKey: ['valuation-items', selectedStockTake, valuationType],
    queryFn: async () => {
      if (!selectedStockTake) return [];
      const response = await api.get(`/api/stock-control/stock-takes/${selectedStockTake}/items/`);
      return response.data.results || response.data;
    },
    enabled: !!selectedStockTake,
  });

  const calculateValuation = () => {
    if (!valuationItems) return 0;
    return valuationItems.reduce((total: number, item: any) => {
      const qty = valuationType === 'actual' ? item.quantity_on_hand : item.quantity_counted;
      return total + qty * item.cost_price_at_count;
    }, 0);
  };

  const totalValuation = calculateValuation();

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
        <h3 className="text-2xl font-bold">Stock Valuation Report</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <label className="block text-sm font-medium mb-2">Select Stock Take</label>
          <select
            value={selectedStockTake}
            onChange={(e) => setSelectedStockTake(e.target.value ? parseInt(e.target.value) : '')}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Select Stock Take --</option>
            {stockTakes?.map((st: any) => (
              <option key={st.id} value={st.id}>
                {st.stock_take_date} ({st.status})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Valuation Type</label>
          <select
            value={valuationType}
            onChange={(e) => setValuationType(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="actual">Actual Qty on Hand</option>
            <option value="counted">Quantity Counted</option>
          </select>
        </div>
      </div>

      {selectedStockTake && (
        <>
          <div className="overflow-x-auto mb-6">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 border-b">
                <tr>
                  <th className="text-left px-4 py-2">Stock Code</th>
                  <th className="text-left px-4 py-2">Description</th>
                  <th className="text-right px-4 py-2">Quantity</th>
                  <th className="text-right px-4 py-2">Cost Price</th>
                  <th className="text-right px-4 py-2">Valuation</th>
                </tr>
              </thead>
              <tbody>
                {valuationItems?.map((item: any, index: number) => {
                  const qty = valuationType === 'actual' ? item.quantity_on_hand : item.quantity_counted;
                  const value = qty * item.cost_price_at_count;
                  return (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-2 font-medium">{item.stock_item?.stock_code}</td>
                      <td className="px-4 py-2">{item.stock_item?.description}</td>
                      <td className="text-right px-4 py-2">{qty.toFixed(2)}</td>
                      <td className="text-right px-4 py-2">R {item.cost_price_at_count.toFixed(2)}</td>
                      <td className="text-right px-4 py-2 font-semibold">R {value.toFixed(2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="mb-6 space-y-2 text-right max-w-md ml-auto">
            <div className="flex justify-between text-lg border-t pt-4">
              <span>Total Stock Valuation:</span>
              <span className="font-bold text-2xl text-blue-600">
                R {totalValuation.toFixed(2)}
              </span>
            </div>
            <p className="text-xs text-gray-500">
              {valuationType === 'actual' 
                ? 'Based on Actual Quantity on Hand' 
                : 'Based on Quantity Counted'}
            </p>
          </div>
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
          Export Valuation
        </button>
      </div>
    </div>
  );
}

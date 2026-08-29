'use client';

import { useState } from 'react';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import type { StockTake } from '@/lib/types/stockControl';

interface StockTakeUpdateProps {
  onBack: () => void;
}

/**
 * "F. Stock Take Update" — apply a stock take's counted quantities to
 * live QOH. Was previously routed to the same component as "G. Stock Item
 * Adjustment" in StockTakeMenu.tsx, so this screen (and update_stock's
 * mode/After-Trading options) had no UI at all.
 */
export default function StockTakeUpdate({ onBack }: StockTakeUpdateProps) {
  const [selectedId, setSelectedId] = useState<number | ''>('');
  const [mode, setMode] = useState<'overwrite' | 'additive'>('overwrite');
  const [resetNegatives, setResetNegatives] = useState(false);
  const [setUncounted, setSetUncounted] = useState(false);
  const [isAfterTrading, setIsAfterTrading] = useState(false);
  const [tradingStartDate, setTradingStartDate] = useState('');
  const queryClient = useQueryClient();

  const { data: stockTakes, isLoading } = useQuery({
    queryKey: ['stock-takes', 'updatable'],
    queryFn: async () => {
      const result = await stockControlApi.stockTakes.list();
      const takes = result.results ?? (result as unknown as StockTake[]);
      return takes.filter((t) => t.status === 'IN_PROGRESS' || t.status === 'COMPLETED');
    },
  });

  const selectedTake = stockTakes?.find((t) => t.id === selectedId);

  const applyFlagsMutation = useMutation({
    mutationFn: async (id: number) =>
      stockControlApi.stockTakes.update(id, {
        reset_negatives_to_zero: resetNegatives,
        set_uncounted_to_zero: setUncounted,
        is_after_trading: isAfterTrading,
        trading_start_date: isAfterTrading && tradingStartDate ? tradingStartDate : undefined,
      }),
  });

  const updateStockMutation = useMutation({
    mutationFn: async (id: number) => stockControlApi.stockTakes.updateStock(id, mode),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['stock-takes'] });
      queryClient.invalidateQueries({ queryKey: ['stock-items'] });
      alert(data?.message ?? 'Stock take applied.');
      onBack();
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.error ?? error?.message ?? 'Unknown error';
      alert(`Update failed: ${msg}`);
    },
  });

  const handleApply = async () => {
    if (!selectedId) {
      alert('Select a stock take first.');
      return;
    }
    if (isAfterTrading && !tradingStartDate) {
      alert('Trading start date is required for an After-Trading update.');
      return;
    }
    if (isAfterTrading && mode === 'additive') {
      alert('Additive mode cannot be combined with an After-Trading update.');
      return;
    }
    await applyFlagsMutation.mutateAsync(selectedId);
    await updateStockMutation.mutateAsync(selectedId);
  };

  const busy = applyFlagsMutation.isPending || updateStockMutation.isPending;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={onBack} className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} />
          Back
        </button>
        <h3 className="text-2xl font-bold">Stock Take Update</h3>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Select Stock Take</label>
        <select
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value ? parseInt(e.target.value) : '')}
          disabled={isLoading}
          className="w-full md:w-96 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">{isLoading ? 'Loading...' : '-- Select Stock Take --'}</option>
          {stockTakes?.map((st) => (
            <option key={st.id} value={st.id}>
              {st.stock_take_date} ({st.status}) — {st.item_count ?? 0} items
            </option>
          ))}
        </select>
        {stockTakes && stockTakes.length === 0 && !isLoading && (
          <p className="text-sm text-gray-500 mt-2">No in-progress or completed stock takes to update.</p>
        )}
      </div>

      {selectedTake && (
        <div className="bg-gray-50 rounded-lg p-6 mb-6 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Update Mode</label>
            <div className="flex gap-6">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={mode === 'overwrite'}
                  onChange={() => setMode('overwrite')}
                />
                Overwrite (counted quantity is the new QOH)
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={mode === 'additive'}
                  disabled={isAfterTrading}
                  onChange={() => setMode('additive')}
                />
                Additive (counted quantity is added to current QOH)
              </label>
            </div>
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={isAfterTrading}
              onChange={(e) => {
                setIsAfterTrading(e.target.checked);
                if (e.target.checked) setMode('overwrite');
              }}
              className="w-4 h-4"
            />
            <span className="text-sm font-medium">
              After-Trading update (sales/receipts happened since the physical count — preserve those movements instead of overwriting them)
            </span>
          </label>

          {isAfterTrading && (
            <div>
              <label className="block text-sm font-medium mb-2">Trading Start Date *</label>
              <input
                type="datetime-local"
                value={tradingStartDate}
                onChange={(e) => setTradingStartDate(e.target.value)}
                className="w-full md:w-72 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={resetNegatives}
              onChange={(e) => setResetNegatives(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm">Reset negative counts to zero</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={setUncounted}
              onChange={(e) => setSetUncounted(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm">Set uncounted items to zero</span>
          </label>
        </div>
      )}

      <div className="flex gap-4 justify-end">
        <button onClick={onBack} className="px-6 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition">
          Cancel
        </button>
        <button
          onClick={handleApply}
          disabled={!selectedId || busy}
          className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
        >
          <RefreshCw size={20} />
          {busy ? 'Applying...' : 'Apply to Stock'}
        </button>
      </div>
    </div>
  );
}

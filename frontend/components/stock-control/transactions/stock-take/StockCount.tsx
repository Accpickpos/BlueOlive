'use client';

import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Save, X, ChevronUp, ChevronDown } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { stockControlApi } from '@/lib/stockControlApi';

interface StockCountProps {
  onBack: () => void;
}

export default function StockCount({ onBack }: StockCountProps) {
  const [stockTakeId, setStockTakeId] = useState<number | null>(null);
  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [countedQuantities, setCountedQuantities] = useState<{ [key: string]: number }>({});
  const [stockItems, setStockItems] = useState<any[]>([]);
  // stock_code -> StockTakeItem id, so re-saving (e.g. after Previous) updates
  // the existing row instead of hitting the (stock_take, stock_item) unique
  // constraint on a second create.
  const savedItemIds = useRef<{ [stockCode: string]: number }>({});

  // Create new stock take session
  const createStockTake = useMutation({
    mutationFn: async () => {
      return stockControlApi.stockTakes.create({
        stock_take_date: new Date().toISOString().split('T')[0],
        status: 'IN_PROGRESS',
        description: 'Physical stock count session',
      });
    },
    onSuccess: (data) => {
      setStockTakeId(data.id);
      loadStockItems();
    },
  });

  // Load stock items for counting
  const loadStockItems = async () => {
    try {
      const response = await api.get('/api/stock-control/stock-items/');
      const items = response.data.results || response.data;
      setStockItems(items.filter((item: any) => item.is_active));
    } catch (error) {
      console.error('Error loading stock items:', error);
    }
  };

  // Save quantity for current item
  const saveQuantity = useMutation({
    mutationFn: async (quantity: number) => {
      if (!stockTakeId || !stockItems[currentItemIndex]) {
        throw new Error('Invalid stock take or item');
      }

      const item = stockItems[currentItemIndex];
      const existingId = savedItemIds.current[item.stock_code];
      if (existingId) {
        return stockControlApi.stockTakeItems.recordCount(existingId, quantity);
      }

      const created = await stockControlApi.stockTakeItems.create({
        stock_take: stockTakeId,
        stock_item: item.stock_code,
        quantity_on_hand: item.quantity_on_hand,
      });
      savedItemIds.current[item.stock_code] = created.id;
      return stockControlApi.stockTakeItems.recordCount(created.id, quantity);
    },
    onSuccess: () => {
      // Move to next item
      if (currentItemIndex < stockItems.length - 1) {
        setCurrentItemIndex(currentItemIndex + 1);
      }
    },
  });

  useEffect(() => {
    if (!stockTakeId) {
      createStockTake.mutate();
    }
  }, []);

  if (!stockItems.length) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6 text-center">
        <p className="text-gray-600">Loading stock items...</p>
      </div>
    );
  }

  const currentItem = stockItems[currentItemIndex];
  const currentQuantity = countedQuantities[currentItem?.stock_code] || 0;

  const handleSave = () => {
    setCountedQuantities({
      ...countedQuantities,
      [currentItem.stock_code]: currentQuantity,
    });
    saveQuantity.mutate(currentQuantity);
  };

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
        <h3 className="text-2xl font-bold">Stock Count</h3>
      </div>

      <div className="mb-6 p-4 bg-gray-100 rounded-lg">
        <p className="text-sm text-gray-600">
          Item <strong>{currentItemIndex + 1}</strong> of <strong>{stockItems.length}</strong>
        </p>
        <div className="w-full bg-gray-300 rounded-full h-2 mt-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{
              width: `${((currentItemIndex + 1) / stockItems.length) * 100}%`,
            }}
          ></div>
        </div>
      </div>

      {currentItem && (
        <div className="bg-gray-50 rounded-lg p-8 mb-6">
          <h4 className="text-lg font-semibold mb-4 text-gray-700">Item Information</h4>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <p className="text-sm text-gray-600">Stock Code</p>
              <p className="text-2xl font-bold">{currentItem.stock_code}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Description</p>
              <p className="text-lg">{currentItem.description}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">System Quantity on Hand</p>
              <p className="text-2xl font-bold text-green-600">{currentItem.quantity_on_hand.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Monthly Sales to Date</p>
              <p className="text-lg">{currentItem.sales_mtd_quantity?.toFixed(2) || '0.00'}</p>
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 border-2 border-blue-500">
            <label className="block text-sm font-medium mb-4">Quantity Counted</label>
            <input
              type="number"
              value={currentQuantity}
              onChange={(e) =>
                setCountedQuantities({
                  ...countedQuantities,
                  [currentItem.stock_code]: parseFloat(e.target.value) || 0,
                })
              }
              step="0.01"
              min="0"
              autoFocus
              className="w-full px-6 py-4 text-3xl font-bold border-2 border-blue-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-700"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSave();
                }
              }}
            />
            <p className="text-xs text-gray-500 mt-2">Press [Enter] to save and move to next item, or click Save</p>
          </div>

          {currentQuantity !== currentItem.quantity_on_hand && (
            <div className="mt-4 p-4 bg-yellow-50 border-l-4 border-yellow-600 rounded">
              <p className="text-sm text-yellow-800">
                <strong>Variance:</strong> Counted {currentQuantity.toFixed(2)} vs System {currentItem.quantity_on_hand.toFixed(2)} 
                ({(currentQuantity - currentItem.quantity_on_hand).toFixed(2)})
              </p>
            </div>
          )}
        </div>
      )}

      <div className="flex gap-4 justify-center">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-6 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition"
        >
          <X size={20} />
          End Count
        </button>

        <button
          onClick={() => setCurrentItemIndex(Math.max(0, currentItemIndex - 1))}
          disabled={currentItemIndex === 0}
          className="flex items-center gap-2 px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition"
        >
          <ChevronUp size={20} />
          Previous
        </button>

        <button
          onClick={handleSave}
          disabled={saveQuantity.isPending}
          className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
        >
          <Save size={20} />
          {saveQuantity.isPending ? 'Saving...' : 'Save & Next'}
        </button>

        <button
          onClick={() =>
            setCurrentItemIndex(Math.min(stockItems.length - 1, currentItemIndex + 1))
          }
          disabled={currentItemIndex === stockItems.length - 1}
          className="flex items-center gap-2 px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition"
        >
          <ChevronDown size={20} />
          Skip
        </button>
      </div>
    </div>
  );
}

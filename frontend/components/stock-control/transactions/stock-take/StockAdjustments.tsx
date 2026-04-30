'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Plus, Trash2, Save, X } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface StockAdjustmentsProps {
  onBack: () => void;
}

export default function StockAdjustments({ onBack }: StockAdjustmentsProps) {
  const [selectedStockCode, setSelectedStockCode] = useState('');
  const [newQuantity, setNewQuantity] = useState(0);
  const [adjustmentReason, setAdjustmentReason] = useState('MANUAL_ADJUSTMENT');
  const [adjustments, setAdjustments] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [stockItems, setStockItems] = useState<any[]>([]);
  const [filteredItems, setFilteredItems] = useState<any[]>([]);
  const [showItemsList, setShowItemsList] = useState(false);
  const queryClient = useQueryClient();

  // Fetch stock items
  const { data: stockData } = useQuery({
    queryKey: ['stock-items'],
    queryFn: async () => {
      const response = await api.get('/api/stock-control/stock-items/');
      return response.data.results || response.data;
    },
  });

  // Create adjustment transaction
  const createAdjustment = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/api/stock-control/transactions/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-items'] });
      alert('Stock adjustment completed successfully!');
      setAdjustments([]);
      onBack();
    },
    onError: (error: any) => {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    },
  });

  useEffect(() => {
    if (stockData) {
      setStockItems(stockData);
    }
  }, [stockData]);

  useEffect(() => {
    if (searchTerm) {
      const filtered = stockItems.filter(
        (item) =>
          item.stock_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredItems(filtered);
      setShowItemsList(true);
    } else {
      setFilteredItems([]);
      setShowItemsList(false);
    }
  }, [searchTerm, stockItems]);

  const handleSelectItem = (item: any) => {
    setSelectedStockCode(item.stock_code);
    setNewQuantity(item.quantity_on_hand);
    setSearchTerm(item.stock_code);
    setShowItemsList(false);
  };

  const handleAddAdjustment = () => {
    if (!selectedStockCode || newQuantity < 0) {
      alert('Please select an item and enter a valid quantity');
      return;
    }

    const item = stockItems.find((s) => s.stock_code === selectedStockCode);
    const currentQty = parseFloat(item?.quantity_on_hand) || 0;
    const difference = newQuantity - currentQty;

    const adjustment = {
      stock_code: selectedStockCode,
      description: item?.description || '',
      current_qty: currentQty,
      new_qty: newQuantity,
      difference,
      reason: adjustmentReason,
    };

    setAdjustments([...adjustments, adjustment]);
    setSelectedStockCode('');
    setNewQuantity(0);
    setSearchTerm('');
    setAdjustmentReason('MANUAL_ADJUSTMENT');
  };

  const handleRemoveAdjustment = (index: number) => {
    setAdjustments(adjustments.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (adjustments.length === 0) {
      alert('Please add at least one adjustment');
      return;
    }

    try {
      for (const adj of adjustments) {
        const transactionData = {
          transaction_type: 'ADJUSTMENT',
          stock_item: adj.stock_code,
          quantity_in: Math.max(0, adj.difference),
          quantity_out: Math.max(0, -adj.difference),
          unit_cost: 0,
          unit_price: 0,
          transaction_date: new Date().toISOString(),
          transaction_number: `ADJ-${Date.now()}`,
          reference: adj.reason,
        };

        await createAdjustment.mutateAsync(transactionData);
      }
    } catch (error) {
      console.error('Error creating adjustment:', error);
    }
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
        <h3 className="text-2xl font-bold">Stock Item Adjustments</h3>
      </div>

      {/* Add Adjustment Section */}
      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <h4 className="text-lg font-semibold mb-4">Add Stock Adjustment</h4>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-2">Stock Code / Description</label>
            <div className="relative">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search stock..."
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {showItemsList && (
                <div className="absolute top-full left-0 right-0 bg-white border border-t-0 rounded-b-lg shadow-lg max-h-40 overflow-y-auto z-10">
                  {filteredItems.map((item) => (
                    <div
                      key={item.stock_code}
                      onClick={() => handleSelectItem(item)}
                      className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
                    >
                      <p className="font-medium">{item.stock_code}</p>
                      <p className="text-sm text-gray-600">{item.description}</p>
                      <p className="text-xs text-gray-500">Current: {item.quantity_on_hand.toFixed(2)}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">New Quantity</label>
            <input
              type="number"
              value={newQuantity}
              onChange={(e) => setNewQuantity(parseFloat(e.target.value) || 0)}
              step="0.01"
              min="0"
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Reason</label>
            <select
              value={adjustmentReason}
              onChange={(e) => setAdjustmentReason(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="MANUAL_ADJUSTMENT">Manual Adjustment</option>
              <option value="STOCK_DISCREPANCY">Stock Discrepancy</option>
              <option value="SHRINKAGE">Shrinkage</option>
              <option value="DAMAGE">Damaged Goods</option>
              <option value="LOST">Lost Stock</option>
              <option value="CORRECTION">Correction</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleAddAdjustment}
              disabled={!selectedStockCode}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <Plus size={20} />
              Add
            </button>
          </div>
        </div>
      </div>

      {/* Adjustments List */}
      <div className="mb-6">
        <h4 className="text-lg font-semibold mb-4">Pending Adjustments</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-100 border-b">
              <tr>
                <th className="text-left px-4 py-2">Stock Code</th>
                <th className="text-left px-4 py-2">Description</th>
                <th className="text-right px-4 py-2">Current Qty</th>
                <th className="text-right px-4 py-2">New Qty</th>
                <th className="text-right px-4 py-2">Difference</th>
                <th className="text-left px-4 py-2">Reason</th>
                <th className="text-center px-4 py-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {adjustments.map((adj, index) => (
                <tr key={index} className={`border-b ${adj.difference > 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                  <td className="px-4 py-2 font-medium">{adj.stock_code}</td>
                  <td className="px-4 py-2">{adj.description}</td>
                  <td className="text-right px-4 py-2">{adj.current_qty.toFixed(2)}</td>
                  <td className="text-right px-4 py-2">{adj.new_qty.toFixed(2)}</td>
                  <td className={`text-right px-4 py-2 font-semibold ${adj.difference > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {adj.difference > 0 ? '+' : ''}{adj.difference.toFixed(2)}
                  </td>
                  <td className="px-4 py-2 text-xs text-gray-600">{adj.reason}</td>
                  <td className="text-center px-4 py-2">
                    <button
                      onClick={() => handleRemoveAdjustment(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {adjustments.length === 0 && (
          <div className="p-4 text-center text-gray-500 bg-gray-50 rounded-lg">
            No adjustments added yet.
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 justify-end">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-6 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition"
        >
          <X size={20} />
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={adjustments.length === 0 || createAdjustment.isPending}
          className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition"
        >
          <Save size={20} />
          {createAdjustment.isPending ? 'Processing...' : 'Apply Adjustments'}
        </button>
      </div>
    </div>
  );
}

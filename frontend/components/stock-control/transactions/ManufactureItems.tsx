'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Save, X, ChevronDown, ChevronUp } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface ManufactureItemsProps {
  onBack: () => void;
}

export default function ManufactureItems({ onBack }: ManufactureItemsProps) {
  const [selectedBundleCode, setSelectedBundleCode] = useState('');
  const [quantityManufactured, setQuantityManufactured] = useState(1);
  const [dateOfManufacture, setDateOfManufacture] = useState(new Date().toISOString().split('T')[0]);
  const [warnOutOfStock, setWarnOutOfStock] = useState(true);
  const [bundles, setBundles] = useState<any[]>([]);
  const [selectedBundle, setSelectedBundle] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredBundles, setFilteredBundles] = useState<any[]>([]);
  const [showBundlesList, setShowBundlesList] = useState(false);
  const queryClient = useQueryClient();

  // Fetch pack bundles
  const { data: bundlesData } = useQuery({
    queryKey: ['pack-bundles'],
    queryFn: async () => {
      const response = await api.get('/api/stock-control/pack-bundles/');
      return response.data.results || response.data;
    },
  });

  // Create manufacture transaction
  const createManufacture = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/api/stock-control/transactions/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pack-bundles'] });
      queryClient.invalidateQueries({ queryKey: ['stock-items'] });
      alert('Manufacturing completed successfully!');
      setSelectedBundleCode('');
      setQuantityManufactured(1);
      setDateOfManufacture(new Date().toISOString().split('T')[0]);
      onBack();
    },
    onError: (error: any) => {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    },
  });

  useEffect(() => {
    if (bundlesData) {
      setBundles(bundlesData);
    }
  }, [bundlesData]);

  useEffect(() => {
    if (searchTerm) {
      const filtered = bundles.filter(
        (bundle) =>
          bundle.stock_item.stock_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
          bundle.stock_item.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredBundles(filtered);
      setShowBundlesList(true);
    } else {
      setFilteredBundles([]);
      setShowBundlesList(false);
    }
  }, [searchTerm, bundles]);

  const handleSelectBundle = (bundle: any) => {
    setSelectedBundleCode(bundle.stock_item.stock_code);
    setSelectedBundle(bundle);
    setSearchTerm(bundle.stock_item.stock_code);
    setShowBundlesList(false);
  };

  const handleSubmit = async () => {
    if (!selectedBundleCode || !quantityManufactured || !dateOfManufacture) {
      alert('Please fill in all required fields');
      return;
    }

    if (!selectedBundle) {
      alert('Please select a valid bundle');
      return;
    }

    try {
      // Check ingredients availability if needed
      const outOfStockItems = selectedBundle.ingredients
        .filter((ing: any) => ing.ingredient_stock.quantity_on_hand < ing.quantity * quantityManufactured)
        .map((ing: any) => ing.ingredient_stock.stock_code);

      if (outOfStockItems.length > 0 && warnOutOfStock) {
        const proceed = window.confirm(
          `Warning: The following items have insufficient stock:\n${outOfStockItems.join(', ')}\n\nDo you want to continue?`
        );
        if (!proceed) return;
      }

      // Create manufacture transaction for bundle
      const bundleTransactionData = {
        transaction_type: 'MANUFACTURE',
        stock_item: selectedBundleCode,
        quantity_in: quantityManufactured,
        unit_cost: selectedBundle.total_cost,
        unit_price: selectedBundle.total_cost,
        transaction_date: new Date(dateOfManufacture).toISOString(),
        transaction_number: `MFG-${Date.now()}`,
        reference: `Manufactured ${quantityManufactured} units`,
      };

      await createManufacture.mutateAsync(bundleTransactionData);

      // Create transactions for each ingredient
      for (const ingredient of selectedBundle.ingredients) {
        const ingredientTransactionData = {
          transaction_type: 'BUNDLE_USE',
          stock_item: ingredient.ingredient_stock.stock_code,
          quantity_out: ingredient.quantity * quantityManufactured,
          unit_cost: ingredient.ingredient_stock.cost_price,
          unit_price: ingredient.ingredient_stock.cost_price,
          transaction_date: new Date(dateOfManufacture).toISOString(),
          transaction_number: `MFG-${Date.now()}`,
          reference: `Used in manufacturing bundle ${selectedBundleCode}`,
        };

        await createManufacture.mutateAsync(ingredientTransactionData);
      }
    } catch (error) {
      console.error('Error creating manufacture transaction:', error);
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
        <h3 className="text-2xl font-bold">Manufacture Item(s)</h3>
      </div>

      {/* Bundle Selection */}
      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <h4 className="text-lg font-semibold mb-4">Select Pack/Bundle</h4>
        <div className="relative mb-4">
          <label className="block text-sm font-medium mb-2">Pack/Bundle Code or Description</label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search bundles..."
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {showBundlesList && (
            <div className="absolute top-full left-0 right-0 bg-white border border-t-0 rounded-b-lg shadow-lg max-h-60 overflow-y-auto z-10 mt-0">
              {filteredBundles.map((bundle) => (
                <div
                  key={bundle.stock_item.stock_code}
                  onClick={() => handleSelectBundle(bundle)}
                  className="px-4 py-3 hover:bg-blue-50 cursor-pointer border-b last:border-b-0"
                >
                  <p className="font-medium">{bundle.stock_item.stock_code}</p>
                  <p className="text-sm text-gray-600">{bundle.stock_item.description}</p>
                  <p className="text-xs text-gray-500">
                    Bundle Cost: R {bundle.total_cost.toFixed(2)} | Current Stock: {bundle.stock_item.quantity_on_hand.toFixed(2)}
                  </p>
                </div>
              ))}
              {filteredBundles.length === 0 && (
                <div className="px-4 py-3 text-gray-500 text-center">No bundles found</div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Bundle Details */}
      {selectedBundle && (
        <div className="bg-blue-50 rounded-lg p-6 mb-6 border-l-4 border-blue-600">
          <h4 className="text-lg font-semibold mb-4">Bundle Details</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <p className="text-sm text-gray-600">Bundle Code</p>
              <p className="text-lg font-bold">{selectedBundle.stock_item.stock_code}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Bundle Total Cost</p>
              <p className="text-lg font-bold text-green-600">R {selectedBundle.total_cost.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Current Stock</p>
              <p className="text-lg font-bold">{selectedBundle.stock_item.quantity_on_hand.toFixed(2)}</p>
            </div>
          </div>

          <h5 className="font-semibold mb-3">Ingredients Required</h5>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-white border-b">
                <tr>
                  <th className="text-left px-4 py-2">Ingredient Code</th>
                  <th className="text-left px-4 py-2">Description</th>
                  <th className="text-right px-4 py-2">Qty per Bundle</th>
                  <th className="text-right px-4 py-2">Current Stock</th>
                  <th className="text-right px-4 py-2">Required for Manufacture</th>
                  <th className="text-center px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {selectedBundle.ingredients?.map((ing: any) => {
                  const required = ing.quantity * quantityManufactured;
                  const available = ing.ingredient_stock.quantity_on_hand;
                  const isAvailable = available >= required;
                  
                  return (
                    <tr key={ing.ingredient_stock.stock_code} className={`border-b ${!isAvailable ? 'bg-red-50' : ''}`}>
                      <td className="px-4 py-2 font-medium">{ing.ingredient_stock.stock_code}</td>
                      <td className="px-4 py-2">{ing.ingredient_stock.description}</td>
                      <td className="text-right px-4 py-2">{ing.quantity.toFixed(2)}</td>
                      <td className="text-right px-4 py-2">{available.toFixed(2)}</td>
                      <td className="text-right px-4 py-2">{required.toFixed(2)}</td>
                      <td className="text-center px-4 py-2">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          isAvailable ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {isAvailable ? 'OK' : 'LOW'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Manufacture Details */}
      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <h4 className="text-lg font-semibold mb-4">Manufacture Details</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Quantity to Manufacture</label>
            <input
              type="number"
              value={quantityManufactured}
              onChange={(e) => setQuantityManufactured(parseInt(e.target.value) || 1)}
              min="1"
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Date of Manufacture</label>
            <input
              type="date"
              value={dateOfManufacture}
              onChange={(e) => setDateOfManufacture(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={warnOutOfStock}
                onChange={(e) => setWarnOutOfStock(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm font-medium">Warn on out of stock</span>
            </label>
          </div>
        </div>
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
          disabled={!selectedBundleCode || createManufacture.isPending}
          className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition"
        >
          <Save size={20} />
          {createManufacture.isPending ? 'Processing...' : 'Confirm Manufacture'}
        </button>
      </div>
    </div>
  );
}

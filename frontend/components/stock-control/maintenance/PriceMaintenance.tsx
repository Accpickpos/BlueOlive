'use client';

import { useState } from 'react';
import { ArrowLeft, Plus, Trash2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface PriceMaintenanceProps {
  onBack: () => void;
}

type PriceOption = 'menu' | 'individual' | 'range-department' | 'range-supplier' | 'future' | 'max-discount' | 'view-discount';

export default function PriceMaintenance({ onBack }: PriceMaintenanceProps) {
  const [selectedOption, setSelectedOption] = useState<PriceOption>('menu');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<any>({});
  const queryClient = useQueryClient();

  const priceOptions = [
    {
      id: 'individual',
      title: 'Individual Stock Items',
      description: 'Adjust cost price, markup %, and selling prices for specific items'
    },
    {
      id: 'range-department',
      title: 'Range of Items - By Department',
      description: 'Apply price adjustments to all items in a department'
    },
    {
      id: 'range-supplier',
      title: 'Range of Items - By Supplier',
      description: 'Apply price adjustments to items from a specific supplier'
    },
    {
      id: 'future',
      title: 'Future Pricing',
      description: 'Set future prices that become active on a specified date'
    },
    {
      id: 'max-discount',
      title: 'Set Maximum Discount',
      description: 'Set maximum discount limits by department or supplier'
    },
    {
      id: 'view-discount',
      title: 'View Maximum Discounts',
      description: 'View current maximum discount settings per supplier'
    }
  ];

  // Fetch stock items
  const { data: stockItems = [] } = useQuery({
    queryKey: ['stock-items'],
    queryFn: async () => {
      const response = await api.get('/api/stock-control/stock-items/');
      return response.data.results || response.data;
    }
  });

  // Fetch departments
  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: async () => {
      const response = await api.get('/api/v1/settings/departments/');
      return response.data.results || response.data;
    }
  });

  // Fetch suppliers
  const { data: suppliers = [] } = useQuery({
    queryKey: ['suppliers'],
    queryFn: async () => {
      const response = await api.get('/api/v1/creditors/creditors/');
      return response.data.results || response.data;
    }
  });

  const handleApplyPriceChange = () => {
    if (!formData.adjustment_type || !formData.adjustment_value) {
      alert('Please fill in all required fields');
      return;
    }
    
    // This would apply bulk price changes - implementation depends on backend endpoint
    console.log('Apply price change:', formData);
    setShowForm(false);
    setFormData({});
  };

  // Individual Stock Items Form
  if (selectedOption === 'individual') {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSelectedOption('menu')}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Menu
          </button>
          <h2 className="text-2xl font-bold text-gray-900">Individual Stock Items - Price Adjustment</h2>
        </div>

        {!showForm ? (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Adjust Price
          </button>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Adjust Individual Item Price</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Stock Code *</label>
                <select
                  value={formData.stock_code || ''}
                  onChange={(e) => setFormData({ ...formData, stock_code: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">-- Select Stock Item --</option>
                  {stockItems.map((item: any) => (
                    <option key={item.stock_code} value={item.stock_code}>
                      {item.stock_code} - {item.description}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Cost Price</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.cost_price || ''}
                    onChange={(e) => setFormData({ ...formData, cost_price: e.target.value ? parseFloat(e.target.value) : 0 })}
                    placeholder="Cost price"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Markup %</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.markup_percent || ''}
                    onChange={(e) => setFormData({ ...formData, markup_percent: e.target.value ? parseFloat(e.target.value) : 0 })}
                    placeholder="Markup percentage"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleApplyPriceChange}
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
                >
                  Apply Changes
                </button>
                <button
                  onClick={() => { setShowForm(false); setFormData({}); }}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Department Range Form
  if (selectedOption === 'range-department') {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSelectedOption('menu')}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Menu
          </button>
          <h2 className="text-2xl font-bold text-gray-900">Price Adjustment by Department</h2>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Apply Price Changes to Department</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Department *</label>
              <select
                value={formData.department_id || ''}
                onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value="">-- Select Department --</option>
                {departments.map((dept: any) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Adjustment Type *</label>
              <select
                value={formData.adjustment_type || ''}
                onChange={(e) => setFormData({ ...formData, adjustment_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value="">-- Select Type --</option>
                <option value="percentage">Percentage (%)</option>
                <option value="fixed">Fixed Amount (R)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Operation</label>
                <select
                  value={formData.operation || '+'}
                  onChange={(e) => setFormData({ ...formData, operation: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="+">Increase (+)</option>
                  <option value="-">Decrease (-)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Value *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.adjustment_value || ''}
                  onChange={(e) => setFormData({ ...formData, adjustment_value: e.target.value ? parseFloat(e.target.value) : 0 })}
                  placeholder="Enter value"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleApplyPriceChange}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
              >
                Apply to Department
              </button>
              <button
                onClick={() => { setSelectedOption('menu'); setFormData({}); }}
                className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Supplier Range Form
  if (selectedOption === 'range-supplier') {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSelectedOption('menu')}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Menu
          </button>
          <h2 className="text-2xl font-bold text-gray-900">Price Adjustment by Supplier</h2>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Apply Price Changes to Supplier Items</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Supplier *</label>
              <select
                value={formData.supplier_id || ''}
                onChange={(e) => setFormData({ ...formData, supplier_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value="">-- Select Supplier --</option>
                {suppliers.map((supp: any) => (
                  <option key={supp.id} value={supp.id}>
                    {supp.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Adjustment Type *</label>
              <select
                value={formData.adjustment_type || ''}
                onChange={(e) => setFormData({ ...formData, adjustment_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value="">-- Select Type --</option>
                <option value="percentage">Percentage (%)</option>
                <option value="fixed">Fixed Amount (R)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Operation</label>
                <select
                  value={formData.operation || '+'}
                  onChange={(e) => setFormData({ ...formData, operation: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="+">Increase (+)</option>
                  <option value="-">Decrease (-)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Value *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.adjustment_value || ''}
                  onChange={(e) => setFormData({ ...formData, adjustment_value: e.target.value ? parseFloat(e.target.value) : 0 })}
                  placeholder="Enter value"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleApplyPriceChange}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
              >
                Apply to Supplier Items
              </button>
              <button
                onClick={() => { setSelectedOption('menu'); setFormData({}); }}
                className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Future Pricing Form
  if (selectedOption === 'future') {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSelectedOption('menu')}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Menu
          </button>
          <h2 className="text-2xl font-bold text-gray-900">Future Pricing</h2>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Set Future Prices</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Stock Code *</label>
              <select
                value={formData.stock_code || ''}
                onChange={(e) => setFormData({ ...formData, stock_code: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value="">-- Select Stock Item --</option>
                {stockItems.map((item: any) => (
                  <option key={item.stock_code} value={item.stock_code}>
                    {item.stock_code} - {item.description}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Future Cost Price</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.future_cost_price || ''}
                  onChange={(e) => setFormData({ ...formData, future_cost_price: e.target.value ? parseFloat(e.target.value) : 0 })}
                  placeholder="Future cost price"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Effective Date *</label>
                <input
                  type="date"
                  value={formData.effective_date || ''}
                  onChange={(e) => setFormData({ ...formData, effective_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleApplyPriceChange}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
              >
                Set Future Price
              </button>
              <button
                onClick={() => { setSelectedOption('menu'); setFormData({}); }}
                className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Set Maximum Discount Form
  if (selectedOption === 'max-discount') {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSelectedOption('menu')}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Menu
          </button>
          <h2 className="text-2xl font-bold text-gray-900">Set Maximum Discount</h2>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Set Maximum Discount Limit</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Apply to *</label>
              <select
                value={formData.apply_to || 'supplier'}
                onChange={(e) => setFormData({ ...formData, apply_to: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value="supplier">Supplier</option>
                <option value="department">Department</option>
              </select>
            </div>

            {formData.apply_to === 'supplier' ? (
              <div>
                <label className="block text-sm font-medium mb-2">Supplier *</label>
                <select
                  value={formData.supplier_id || ''}
                  onChange={(e) => setFormData({ ...formData, supplier_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">-- Select Supplier --</option>
                  {suppliers.map((supp: any) => (
                    <option key={supp.id} value={supp.id}>
                      {supp.name}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium mb-2">Department *</label>
                <select
                  value={formData.department_id || ''}
                  onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">-- Select Department --</option>
                  {departments.map((dept: any) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-2">Maximum Discount % *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={formData.max_discount_percent || ''}
                onChange={(e) => setFormData({ ...formData, max_discount_percent: e.target.value ? parseFloat(e.target.value) : 0 })}
                placeholder="Maximum discount percentage"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleApplyPriceChange}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
              >
                Set Maximum Discount
              </button>
              <button
                onClick={() => { setSelectedOption('menu'); setFormData({}); }}
                className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // View Maximum Discounts
  if (selectedOption === 'view-discount') {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSelectedOption('menu')}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Menu
          </button>
          <h2 className="text-2xl font-bold text-gray-900">View Maximum Discounts</h2>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Current Maximum Discount Settings</h3>
          
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Filter by Supplier</label>
            <select
              value={formData.filter_supplier || ''}
              onChange={(e) => setFormData({ ...formData, filter_supplier: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">-- All Suppliers --</option>
              {suppliers.map((supp: any) => (
                <option key={supp.id} value={supp.id}>
                  {supp.name}
                </option>
              ))}
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Supplier/Department</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Type</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Maximum Discount %</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {suppliers.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                      No maximum discount settings found
                    </td>
                  </tr>
                ) : (
                  suppliers.map((supp: any) => (
                    <tr key={supp.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{supp.name}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">Supplier</td>
                      <td className="px-6 py-4 text-sm text-gray-600">10%</td>
                      <td className="px-6 py-4 text-sm">
                        <button
                          onClick={() => {
                            setFormData({ supplier_id: supp.id, max_discount_percent: 10 });
                            setSelectedOption('max-discount');
                          }}
                          className="text-blue-600 hover:text-blue-800 mr-4"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => alert('Delete discount for ' + supp.name)}
                          className="text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="mt-6 flex gap-3">
            <button
              onClick={() => setSelectedOption('menu')}
              className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
            >
              Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Default menu view
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <h2 className="text-2xl font-bold text-gray-900">Prices - Maintenance</h2>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {priceOptions.map((option) => (
          <div
            key={option.id}
            onClick={() => setSelectedOption(option.id as PriceOption)}
            className="p-6 bg-white border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition-all cursor-pointer group"
          >
            <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
              {option.title}
            </h3>
            <p className="text-sm text-gray-600 mt-2">{option.description}</p>
            <div className="mt-4 flex items-center gap-2 text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="text-sm">Select</span>
              <span>→</span>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">Price Maintenance Guide</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>- Adjust cost prices (exclusive of VAT)</li>
          <li>- Set markup percentages to automatically calculate selling prices</li>
          <li>- Apply increases or decreases by percentage or rand value</li>
          <li>- Set different prices for up to 3 price levels</li>
          <li>- Future pricing automatically updates after day end procedures</li>
        </ul>
      </div>
    </div>
  );
}
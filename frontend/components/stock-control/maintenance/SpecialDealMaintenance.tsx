'use client';

import { useState } from 'react';
import { ArrowLeft, Plus, Search, Edit2, Trash2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface SpecialDeal {
  id?: string;
  stock_code: string;
  stock_description?: string;
  cost_price: number;
  special_cost_price: number;
  special_selling_price_1?: number;
  special_selling_price_2?: number;
  special_selling_price_3?: number;
  special_markup_1?: number;
  special_markup_2?: number;
  special_markup_3?: number;
  start_date: string;
  end_date: string;
  markup_percentage: number;
  type: 'individual' | 'department';
  department?: string;
  increase_decrease?: '+' | '-';
  percentage_rand?: 'P' | 'R';
  amount?: number;
  sales_price_levels?: string;
}

interface SpecialDealMaintenanceProps {
  onBack: () => void;
}

export default function SpecialDealMaintenance({ onBack }: SpecialDealMaintenanceProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [dealType, setDealType] = useState<'individual' | 'department'>('individual');
  const [editingId, setEditingId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<SpecialDeal>({
    stock_code: '',
    cost_price: 0,
    special_cost_price: 0,
    start_date: '',
    end_date: '',
    markup_percentage: 0,
    type: 'individual',
    department: '',
    increase_decrease: '+',
    percentage_rand: 'P',
    amount: 0,
    sales_price_levels: ''
  });

  // Helper function to calculate selling prices from markup percentage
  const calculateSellingPrices = (costPrice: number, markupPercent: number) => {
    if (!costPrice || !markupPercent) return { price1: 0, price2: 0, price3: 0 };
    const markup = markupPercent / 100;
    const sellingPrice = costPrice * (1 + markup);
    return {
      price1: Math.round(sellingPrice * 100) / 100,
      price2: Math.round(sellingPrice * 100) / 100,
      price3: Math.round(sellingPrice * 100) / 100
    };
  };

  // Helper function to calculate markup from selling price
  const calculateMarkup = (costPrice: number, sellingPrice: number) => {
    if (!costPrice || !sellingPrice) return 0;
    const markup = ((sellingPrice - costPrice) / costPrice) * 100;
    return Math.round(markup * 100) / 100;
  };

  // Handle markup percentage change
  const handleMarkupChange = (value: number) => {
    setFormData({ ...formData, markup_percentage: value });
    const prices = calculateSellingPrices(formData.special_cost_price, value);
    setFormData(prev => ({
      ...prev,
      markup_percentage: value,
      special_selling_price_1: prices.price1,
      special_selling_price_2: prices.price2,
      special_selling_price_3: prices.price3
    }));
  };

  // Handle selling price change
  const handleSellingPriceChange = (priceLevel: 1 | 2 | 3, value: number) => {
    const priceKey = `special_selling_price_${priceLevel}` as keyof SpecialDeal;
    setFormData(prev => ({
      ...prev,
      [priceKey]: value
    }));
    
    // Recalculate markup based on first price level
    if (priceLevel === 1) {
      const newMarkup = calculateMarkup(formData.special_cost_price, value);
      setFormData(prev => ({
        ...prev,
        markup_percentage: newMarkup
      }));
    }
  };

  // Fetch special deals
  const { data: deals = [], isLoading, error } = useQuery({
    queryKey: ['special-deals'],
    queryFn: async () => {
      const response = await api.get('/api/stock-control/special-deals/');
      return response.data.results || response.data;
    }
  });

  // Create/Update mutation
  const mutation = useMutation({
    mutationFn: async (data: SpecialDeal) => {
      if (editingId) {
        return api.put(`/api/stock-control/special-deals/${editingId}/`, data);
      } else {
        return api.post('/api/stock-control/special-deals/', data);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['special-deals'] });
      setShowForm(false);
      setEditingId(null);
      setFormData({
        stock_code: '',
        cost_price: 0,
        special_cost_price: 0,
        start_date: '',
        end_date: '',
        markup_percentage: 0,
        type: 'individual',
        department: '',
        increase_decrease: '+',
        percentage_rand: 'P',
        amount: 0,
        sales_price_levels: ''
      });
    }
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/api/stock-control/special-deals/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['special-deals'] });
    }
  });

  const handleEdit = (deal: SpecialDeal) => {
    setFormData(deal);
    setEditingId(deal.id || '');
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Transform form data to backend format
    const submitData: any = {
      stock_item: formData.stock_code, // Backend expects stock_item with stock code
      special_cost_price: formData.special_cost_price,
      start_date: formData.start_date,
      end_date: formData.end_date,
      is_active: true,
    };

    // Calculate selling prices based on markup_percentage if using individual pricing
    if (dealType === 'individual' && formData.markup_percentage) {
      // Use markup_percentage to calculate selling prices from special_cost_price
      const markup = formData.markup_percentage / 100;
      const basePrice = formData.special_cost_price * (1 + markup);
      submitData.special_selling_price_1 = basePrice;
      submitData.special_selling_price_2 = basePrice;
      submitData.special_selling_price_3 = basePrice;
      submitData.special_markup_1 = formData.markup_percentage;
      submitData.special_markup_2 = formData.markup_percentage;
      submitData.special_markup_3 = formData.markup_percentage;
    } else if (dealType === 'department' && formData.amount) {
      // For department deals, apply amount change across all price levels
      const changeAmount = formData.increase_decrease === '+' ? formData.amount : -formData.amount;
      const isPercentage = formData.percentage_rand === 'P';
      
      // These would be applied per item in a department, so just store the amount
      submitData.special_cost_price = formData.special_cost_price;
      submitData.special_selling_price_1 = formData.amount;
      submitData.special_selling_price_2 = formData.amount;
      submitData.special_selling_price_3 = formData.amount;
    }

    mutation.mutate(submitData);
  };

  const filteredDeals = deals.filter((deal: SpecialDeal) => {
    const searchValue = (deal.stock_code || deal.department || '').toLowerCase();
    return searchValue.includes(searchTerm.toLowerCase());
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Menu
        </button>
        <h2 className="text-2xl font-bold text-gray-900">Special Deal Maintenance</h2>
        <button
          onClick={() => {
            setShowForm(!showForm);
            setEditingId(null);
            setFormData({
              stock_code: '',
              cost_price: 0,
              special_cost_price: 0,
              start_date: '',
              end_date: '',
              markup_percentage: 0,
              type: 'individual',
              department: '',
              increase_decrease: '+',
              percentage_rand: 'P',
              amount: 0,
              sales_price_levels: ''
            });
          }}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          New Deal
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingId ? 'Edit Special Deal' : 'Create New Special Deal'}
          </h3>
          
          <div className="mb-4 flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                value="individual"
                checked={dealType === 'individual'}
                onChange={(e) => {
                  setDealType(e.target.value as 'individual' | 'department');
                  setFormData({ ...formData, type: 'individual' });
                }}
              />
              Individual Stock Items
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                value="department"
                checked={dealType === 'department'}
                onChange={(e) => {
                  setDealType(e.target.value as 'individual' | 'department');
                  setFormData({ ...formData, type: 'department' });
                }}
              />
              Entire Departments
            </label>
          </div>

          <form onSubmit={handleSubmit} className="grid md:grid-cols-2 gap-4">
            {dealType === 'individual' ? (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Stock Code *
                  </label>
                  <input
                    type="text"
                    value={formData.stock_code}
                    onChange={(e) => setFormData({ ...formData, stock_code: e.target.value })}
                    placeholder="Stock code"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Special Cost Price *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.special_cost_price || ''}
                    onChange={(e) => setFormData({ ...formData, special_cost_price: e.target.value ? parseFloat(e.target.value) : 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Mark-up % *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.markup_percentage || ''}
                    onChange={(e) => handleMarkupChange(e.target.value ? parseFloat(e.target.value) : 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Selling Price Level 1 (Recommended)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.special_selling_price_1 || ''}
                    onChange={(e) => handleSellingPriceChange(1, e.target.value ? parseFloat(e.target.value) : 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Selling Price Level 2
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.special_selling_price_2 || ''}
                    onChange={(e) => handleSellingPriceChange(2, e.target.value ? parseFloat(e.target.value) : 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Selling Price Level 3
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.special_selling_price_3 || ''}
                    onChange={(e) => handleSellingPriceChange(3, e.target.value ? parseFloat(e.target.value) : 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                  />
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Department *
                  </label>
                  <input
                    type="text"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    placeholder="Department"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Increase/Decrease *
                  </label>
                  <select
                    value={formData.increase_decrease || '+'}
                    onChange={(e) => setFormData({ ...formData, increase_decrease: e.target.value as '+' | '-' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="+">Increase (+)</option>
                    <option value="-">Decrease (-)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Percentage/Rand *
                  </label>
                  <select
                    value={formData.percentage_rand || 'P'}
                    onChange={(e) => setFormData({ ...formData, percentage_rand: e.target.value as 'P' | 'R' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="P">Percentage (%)</option>
                    <option value="R">Rand Value (R)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Amount *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.amount || ''}
                    onChange={(e) => setFormData({ ...formData, amount: e.target.value ? parseFloat(e.target.value) : 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sales Price Levels (e.g., 1,2,3 or 9 for all)
                  </label>
                  <input
                    type="text"
                    value={formData.sales_price_levels || ''}
                    onChange={(e) => setFormData({ ...formData, sales_price_levels: e.target.value })}
                    placeholder="1,2,3 or 9"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date *
              </label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date *
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              />
            </div>

            <div className="md:col-span-2 flex gap-3">
              <button
                type="submit"
                disabled={mutation.isPending}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {mutation.isPending ? 'Saving...' : editingId ? 'Update Deal' : 'Create Deal'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search by stock code..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
        <table className="w-full">
          <thead className="border-b border-gray-200 bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Code/Dept</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Type</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Start Date</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">End Date</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Markup %</th>
              <th className="px-6 py-3 text-right text-sm font-semibold text-gray-900">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">Loading...</td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-red-500">Error loading deals: {(error as any).message}</td>
              </tr>
            ) : filteredDeals.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">No special deals found</td>
              </tr>
            ) : (
              filteredDeals.map((deal: SpecialDeal) => (
                <tr key={deal.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{deal.stock_code || deal.department}</td>
                  <td className="px-6 py-4 text-sm text-gray-600 capitalize">{deal.type}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{deal.start_date}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{deal.end_date}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{deal.markup_percentage ? `${deal.markup_percentage}%` : (deal.special_markup_1 ? `${deal.special_markup_1}%` : '-')}</td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button
                      onClick={() => handleEdit(deal)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deal.id && deleteMutation.mutate(deal.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
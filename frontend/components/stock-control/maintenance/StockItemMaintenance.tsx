'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Plus, Search, Edit2, Trash2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthContext } from '@/lib/AuthContext';

interface Supplier {
  id: number;
  name: string;
}

interface TaxCode {
  id: number;
  code: string;
  description?: string;
  rate?: number;
}

interface Department {
  id: number;
  name: string;
  department_number?: number;
}

interface StockItem {
  stock_code: string;
  description: string;
  department: string | number;
  supplier?: string | number;
  supplier_code?: string;
  tax_code: string | number;
  reorder_quantity: number;
  cost_price: number;
  allow_negative_quantities: boolean;
  bin_number?: string;
  markup_1?: number;
  markup_2?: number;
  markup_3?: number;
  selling_price_1?: number;
  selling_price_2?: number;
  selling_price_3?: number;
  maximum_discount_percent?: number;
  default_selling_quantity?: number;
  is_active?: boolean;
}

interface StockItemMaintenanceProps {
  onBack: () => void;
}

export default function StockItemMaintenance({ onBack }: StockItemMaintenanceProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingCode, setEditingCode] = useState<string | null>(null);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [taxCodes, setTaxCodes] = useState<TaxCode[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loadingDeps, setLoadingDeps] = useState(true);
  const [depsError, setDepsError] = useState<string>('');
  const [vatRate, setVatRate] = useState<number>(15);
  const queryClient = useQueryClient();
  const { isAuthenticated, isLoading: authLoading } = useAuthContext();

  const [formData, setFormData] = useState<StockItem>({
    stock_code: '',
    description: '',
    department: '',
    supplier: '',
    supplier_code: '',
    tax_code: '',
    reorder_quantity: 0,
    cost_price: 0,
    allow_negative_quantities: false,
    bin_number: '',
    markup_1: 0,
    markup_2: 0,
    markup_3: 0,
    selling_price_1: 0,
    selling_price_2: 0,
    selling_price_3: 0,
    maximum_discount_percent: 0,
    default_selling_quantity: 1,
    is_active: true
  });

  // Load dependencies on mount, but only after auth is confirmed
  useEffect(() => {
    if (authLoading) {
      // Still loading auth, don't try to load dependencies yet
      return;
    }

    if (!isAuthenticated) {
      setDepsError('Please log in to access this feature');
      setLoadingDeps(false);
      return;
    }

    const loadDependencies = async () => {
      try {
        setLoadingDeps(true);
        setDepsError('');
        
        const [suppliersRes, taxRes, deptRes] = await Promise.all([
          api.get('/api/creditors/suppliers/'),
          api.get('/api/settings/tax-codes/'),
          api.get('/api/settings/departments/')
        ]);
        
        setSuppliers(suppliersRes.data.results || suppliersRes.data || []);
        setTaxCodes(taxRes.data.results || taxRes.data || []);
        setDepartments(deptRes.data.results || deptRes.data || []);
      } catch (err: any) {
        console.error('Error loading dependencies:', err);
        if (err.response?.status === 401) {
          setDepsError('Session expired. Please log in again.');
        } else if (err.response?.status === 403) {
          setDepsError('You do not have permission to access this data.');
        } else {
          setDepsError(err.response?.data?.message || err.message || 'Failed to load dependencies. Please try again.');
        }
      } finally {
        setLoadingDeps(false);
      }
    };

    loadDependencies();
  }, [authLoading, isAuthenticated]);

  // Fetch stock items
  const { data: stockItems = [], isLoading, error: stockError } = useQuery({
    queryKey: ['stock-items'],
    queryFn: async () => {
      try {
        const response = await api.get('/api/stock-control/stock-items/');
        return response.data.results || response.data || [];
      } catch (err: any) {
        // If endpoint doesn't exist (404), return empty array instead of failing
        if (err.response?.status === 404) {
          console.warn('Stock items endpoint not found. This endpoint may not be implemented on the backend.');
          return [];
        }
        throw err;
      }
    },
    enabled: isAuthenticated && !authLoading,
  });

  // Helper functions for calculations
  const calculateSellingPrices = (costPrice: number, markupPercent: number) => {
    if (!costPrice || !markupPercent) return 0;
    const markup = markupPercent / 100;
    const sellingPrice = costPrice * (1 + markup);
    return Math.round(sellingPrice * 100) / 100;
  };

  const calculateMarkup = (costPrice: number, sellingPrice: number) => {
    if (!costPrice || !sellingPrice) return 0;
    const markup = ((sellingPrice - costPrice) / costPrice) * 100;
    return Math.round(markup * 100) / 100;
  };

  const calculatePriceInclusive = (price: number, vat: number) => {
    const inclusive = price * (1 + vat / 100);
    return Math.round(inclusive * 100) / 100;
  };

  const calculateGP = (costPrice: number, sellingPrice: number) => {
    if (!sellingPrice) return 0;
    const gp = ((sellingPrice - costPrice) / sellingPrice) * 100;
    return Math.round(gp * 100) / 100;
  };

  // Handle markup change
  const handleMarkupChange = (level: 1 | 2 | 3, value: number) => {
    const markupKey = `markup_${level}` as keyof StockItem;
    const priceKey = `selling_price_${level}` as keyof StockItem;
    
    const newPrice = calculateSellingPrices(formData.cost_price, value);
    
    setFormData(prev => ({
      ...prev,
      [markupKey]: value,
      [priceKey]: newPrice
    }));
  };

  // Handle selling price change
  const handlePriceChange = (level: 1 | 2 | 3, value: number) => {
    const priceKey = `selling_price_${level}` as keyof StockItem;
    const markupKey = `markup_${level}` as keyof StockItem;
    
    const newMarkup = calculateMarkup(formData.cost_price, value);
    
    setFormData(prev => ({
      ...prev,
      [priceKey]: value,
      [markupKey]: newMarkup
    }));
  };

  // Create/Update mutation
  const mutation = useMutation({
    mutationFn: async (data: StockItem) => {
      if (editingCode) {
        return api.put(`/api/stock-control/stock-items/${editingCode}/`, data);
      } else {
        return api.post('/api/stock-control/stock-items/', data);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-items'] });
      setShowForm(false);
      setEditingCode(null);
      resetForm();
    }
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (code: string) => {
      return api.delete(`/api/stock-control/stock-items/${code}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-items'] });
    }
  });

  const resetForm = () => {
    setFormData({
      stock_code: '',
      description: '',
      department: '',
      supplier: '',
      supplier_code: '',
      tax_code: '',
      reorder_quantity: 0,
      cost_price: 0,
      allow_negative_quantities: false,
      bin_number: '',
      markup_1: 0,
      markup_2: 0,
      markup_3: 0,
      selling_price_1: 0,
      selling_price_2: 0,
      selling_price_3: 0,
      maximum_discount_percent: 0,
      default_selling_quantity: 1,
      is_active: true
    });
  };

  const handleEdit = (item: StockItem) => {
    setFormData(item);
    setEditingCode(item.stock_code);
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  const filteredItems = stockItems.filter((item: StockItem) =>
    (item.stock_code?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (item.description?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

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
        <h2 className="text-2xl font-bold text-gray-900">Stock Item Maintenance</h2>
        <button
          onClick={() => {
            setShowForm(!showForm);
            setEditingCode(null);
            resetForm();
          }}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          New Item
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 max-h-[80vh] overflow-y-auto">
          <h3 className="text-lg font-semibold mb-4">
            {editingCode ? 'Edit Stock Item' : 'Create New Stock Item'}
          </h3>

          {depsError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
              <p className="font-semibold">Error Loading Dependencies</p>
              <p className="text-sm">{depsError}</p>
            </div>
          )}

          {loadingDeps && (
            <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-lg mb-4">
              Loading suppliers, departments, and tax codes...
            </div>
          )}

          <form onSubmit={handleSubmit} className="grid md:grid-cols-3 gap-4">
            {/* Basic Information */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stock Code *</label>
              <input
                type="text"
                value={formData.stock_code}
                onChange={(e) => setFormData({ ...formData, stock_code: e.target.value })}
                disabled={!!editingCode}
                placeholder="Stock code"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
                required
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Item Description *</label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Item description"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              />
            </div>

            {/* Department, Tax, Supplier */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Department *</label>
              <select
                value={formData.department || ''}
                onChange={(e) => setFormData({ ...formData, department: e.target.value ? Number(e.target.value) : '' })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value="">Select Department</option>
                {departments.map((dept, idx) => (
                  <option key={`dept-${dept.id}-${idx}`} value={dept.id}>{dept.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tax Code *</label>
              <select
                value={formData.tax_code || ''}
                onChange={(e) => {
                  const selectedTaxId = e.target.value ? Number(e.target.value) : '';
                  setFormData({ ...formData, tax_code: selectedTaxId });
                  
                  // Find the selected tax code and use its rate
                  const selectedTax = taxCodes.find(tax => tax.id === selectedTaxId);
                  if (selectedTax && selectedTax.rate !== undefined) {
                    setVatRate(Number(selectedTax.rate));
                    console.log(`Tax code selected: ${selectedTax.code}, VAT Rate: ${selectedTax.rate}%`);
                  } else {
                    console.warn(`No rate found for tax code: ${selectedTaxId}`);
                    setVatRate(15); // Fallback to 15%
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value="">Select Tax Code</option>
                {taxCodes.map((tax, idx) => (
                  <option key={`tax-${tax.id}-${idx}`} value={tax.id}>
                    {tax.code} {tax.description && `(${tax.description})`} {tax.rate !== undefined && `- ${tax.rate}%`}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Selected VAT Rate: <span className="font-bold text-blue-600">{vatRate}%</span>
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Supplier</label>
              <select
                value={formData.supplier || ''}
                onChange={(e) => setFormData({ ...formData, supplier: e.target.value ? Number(e.target.value) : '' })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">Select Supplier</option>
                {suppliers.map((sup, idx) => (
                  <option key={`supplier-${sup.id}-${idx}`} value={sup.id}>{sup.name}</option>
                ))}
              </select>
            </div>

            {/* Supplier Code & Costs */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Supplier Code</label>
              <input
                type="text"
                value={formData.supplier_code || ''}
                onChange={(e) => setFormData({ ...formData, supplier_code: e.target.value })}
                placeholder="Supplier's code"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cost Price *</label>
              <input
                type="number"
                step="0.01"
                value={formData.cost_price || ''}
                onChange={(e) => setFormData({ ...formData, cost_price: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Re-order Quantity</label>
              <input
                type="number"
                step="0.01"
                value={formData.reorder_quantity || ''}
                onChange={(e) => setFormData({ ...formData, reorder_quantity: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Default Selling Quantity</label>
              <input
                type="number"
                step="0.01"
                value={formData.default_selling_quantity || 1}
                onChange={(e) => setFormData({ ...formData, default_selling_quantity: parseFloat(e.target.value) || 1 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            {/* Stock Control */}
            <div className="flex items-center">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.allow_negative_quantities || false}
                  onChange={(e) => setFormData({ ...formData, allow_negative_quantities: e.target.checked })}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium text-gray-700">Allow Negative Qty</span>
              </label>
            </div>

            {/* Location & Classification */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Bin/Shelf Location</label>
              <input
                type="text"
                value={formData.bin_number || ''}
                onChange={(e) => setFormData({ ...formData, bin_number: e.target.value })}
                placeholder="e.g., A-01-02"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            {/* Pricing Section */}
            <div className="md:col-span-3 border-t pt-4 mt-4">
              <h4 className="text-md font-semibold text-gray-900 mb-4">Pricing & Markup - Enter Markup % to Calculate Selling Prices</h4>
              <div className="grid md:grid-cols-3 gap-6">
                {[1, 2, 3].map((level) => {
                  const markupKey = `markup_${level}` as keyof StockItem;
                  const priceKey = `selling_price_${level}` as keyof StockItem;
                  const priceInc = calculatePriceInclusive(formData[priceKey] as number || 0, vatRate);
                  const gp = calculateGP(formData.cost_price, formData[priceKey] as number || 0);

                  return (
                    <div key={level} className="border border-gray-200 rounded-lg p-4 bg-blue-50">
                      <h5 className="font-semibold text-gray-900 mb-4">Price Level {level}</h5>
                      
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Enter Markup %</label>
                        <input
                          type="number"
                          step="0.01"
                          value={formData[markupKey] || ''}
                          onChange={(e) => handleMarkupChange(level as 1 | 2 | 3, parseFloat(e.target.value) || 0)}
                          placeholder="Enter markup percentage"
                          className="w-full px-3 py-2 border border-blue-300 rounded-lg bg-white font-semibold text-lg text-center"
                        />
                        <p className="text-xs text-gray-600 mt-1">Edit this to auto-calculate selling price</p>
                      </div>

                      <div className="mb-4 p-3 bg-white rounded border border-gray-200">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Selling Price (Auto-Calculated)</label>
                        <input
                          type="number"
                          step="0.01"
                          value={formData[priceKey] || ''}
                          disabled
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-700 font-semibold text-lg"
                        />
                      </div>

                      <div className="mb-4 p-3 bg-green-50 rounded border border-green-200">
                        <label className="block text-xs font-medium text-gray-700 mb-2">Price (Incl. VAT {vatRate}%)</label>
                        <div className="text-lg font-bold text-green-700">R {priceInc.toFixed(2)}</div>
                      </div>

                      <div className="p-3 bg-orange-50 rounded border border-orange-200">
                        <label className="block text-xs font-medium text-gray-700 mb-2">Gross Profit %</label>
                        <div className="text-lg font-bold text-orange-700">{gp.toFixed(2)}%</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Additional Settings */}
            <div className="md:col-span-3 border-t pt-4 mt-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Maximum Discount %</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.maximum_discount_percent || ''}
                    onChange={(e) => setFormData({ ...formData, maximum_discount_percent: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div className="flex items-center">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_active !== false}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <span className="text-sm font-medium text-gray-700">Active</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Form Actions */}
            <div className="md:col-span-3 flex gap-3 mt-6">
              <button
                type="submit"
                disabled={mutation.isPending || loadingDeps || !!depsError}
                title={depsError ? 'Dependencies failed to load. Fix the errors above before submitting.' : loadingDeps ? 'Loading dependencies...' : undefined}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {mutation.isPending ? 'Saving...' : editingCode ? 'Update Item' : 'Create Item'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  resetForm();
                }}
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
          placeholder="Search by stock code or description..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-200 bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-gray-900">Code</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-900">Description</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-900">Department</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-900">Cost</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-900">Price L1</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-900">Price L2</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-900">Price L3</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-900">Reorder</th>
              <th className="px-6 py-3 text-right font-semibold text-gray-900">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {authLoading || loadingDeps ? (
              <tr>
                <td colSpan={10} className="px-6 py-4 text-center text-gray-500">Loading dependencies...</td>
              </tr>
            ) : !isAuthenticated ? (
              <tr>
                <td colSpan={10} className="px-6 py-4 text-center text-red-500">Please log in to view stock items</td>
              </tr>
            ) : depsError ? (
              <tr>
                <td colSpan={10} className="px-6 py-4 text-center text-red-500">{depsError}</td>
              </tr>
            ) : isLoading ? (
              <tr>
                <td colSpan={10} className="px-6 py-4 text-center text-gray-500">Loading stock items...</td>
              </tr>
            ) : stockError ? (
              <tr>
                <td colSpan={10} className="px-6 py-4 text-center text-red-500">Error loading stock items. The backend endpoint may not be configured.</td>
              </tr>
            ) : filteredItems.length === 0 ? (
              <tr>
                <td colSpan={10} className="px-6 py-4 text-center text-gray-500">No stock items found</td>
              </tr>
            ) : (
              filteredItems.map((item: StockItem) => (
                <tr key={item.stock_code} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{item.stock_code}</td>
                  <td className="px-6 py-4 text-gray-600">{item.description}</td>
                  <td className="px-6 py-4 text-gray-600">{item.department}</td>
                  <td className="px-6 py-4 text-gray-600">R {Number(item.cost_price || 0).toFixed(2)}</td>
                  <td className="px-6 py-4 text-gray-600">R {Number(item.selling_price_1 || 0).toFixed(2)}</td>
                  <td className="px-6 py-4 text-gray-600">R {Number(item.selling_price_2 || 0).toFixed(2)}</td>
                  <td className="px-6 py-4 text-gray-600">R {Number(item.selling_price_3 || 0).toFixed(2)}</td>
                  <td className="px-6 py-4 text-gray-600">{Number(item.reorder_quantity || 0).toFixed(2)}</td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button
                      onClick={() => handleEdit(item)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => item.stock_code && deleteMutation.mutate(item.stock_code)}
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

'use client';

import { useState } from 'react';
import { ArrowLeft, Plus, Search, Edit2, Trash2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import type { ContractPricing } from '@/lib/types/stockControl';

interface ContractPricingMaintenanceProps {
  onBack: () => void;
}

type FormState = {
  id?: number;
  debtor: string;
  scope: 'stock_item' | 'department' | 'supplier';
  stock_item: string;
  department: string;
  supplier: string;
  pricing_method: 'ACTUAL' | 'COST_MARKUP';
  contract_price: string;
  markup_percent: string;
  discount_percent: string;
  valid_from: string;
  valid_until: string;
  is_fixed_pricing: boolean;
};

const emptyForm: FormState = {
  debtor: '',
  scope: 'stock_item',
  stock_item: '',
  department: '',
  supplier: '',
  pricing_method: 'ACTUAL',
  contract_price: '',
  markup_percent: '',
  discount_percent: '0',
  valid_from: '',
  valid_until: '',
  is_fixed_pricing: false,
};

export default function ContractPricingMaintenance({ onBack }: ContractPricingMaintenanceProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<FormState>(emptyForm);
  const queryClient = useQueryClient();

  const { data: contracts = [], isLoading, error } = useQuery({
    queryKey: ['contract-pricing'],
    queryFn: async () => {
      const result = await stockControlApi.contractPricing.list();
      return result.results ?? (result as unknown as ContractPricing[]);
    },
  });

  const mutation = useMutation({
    mutationFn: async (payload: Partial<ContractPricing>) => {
      if (editingId) {
        return stockControlApi.contractPricing.update(editingId, payload);
      }
      return stockControlApi.contractPricing.create(payload as Partial<ContractPricing>);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contract-pricing'] });
      setShowForm(false);
      setEditingId(null);
      setFormData(emptyForm);
    },
    onError: (err: any) => {
      const data = err?.response?.data;
      const msg = data && typeof data === 'object'
        ? Object.entries(data).map(([k, v]: any) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')
        : err?.message ?? 'Unknown error';
      alert(`Save failed: ${msg}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => stockControlApi.contractPricing.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contract-pricing'] });
    },
  });

  const handleEdit = (contract: ContractPricing) => {
    setEditingId(contract.id);
    setFormData({
      id: contract.id,
      debtor: String(contract.debtor ?? ''),
      scope: contract.stock_item ? 'stock_item' : contract.department ? 'department' : 'supplier',
      stock_item: contract.stock_item ?? '',
      department: contract.department != null ? String(contract.department) : '',
      supplier: contract.supplier != null ? String(contract.supplier) : '',
      pricing_method: contract.pricing_method,
      contract_price: contract.contract_price != null ? String(contract.contract_price) : '',
      markup_percent: contract.markup_percent != null ? String(contract.markup_percent) : '',
      discount_percent: contract.discount_percent != null ? String(contract.discount_percent) : '0',
      valid_from: contract.valid_from ?? '',
      valid_until: contract.valid_until ?? '',
      is_fixed_pricing: !!contract.is_fixed_pricing,
    });
    setShowForm(true);
  };

  const handleNew = () => {
    setEditingId(null);
    setFormData(emptyForm);
    setShowForm(!showForm);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.debtor.trim()) {
      alert('Debtor account number is required.');
      return;
    }
    if (formData.scope === 'stock_item' && !formData.stock_item.trim()) {
      alert('Stock code is required for item-specific pricing.');
      return;
    }
    if (formData.scope === 'department' && !formData.department.trim()) {
      alert('Department is required for department-based pricing.');
      return;
    }
    if (formData.scope === 'supplier' && !formData.supplier.trim()) {
      alert('Supplier is required for supplier-based pricing.');
      return;
    }
    if (formData.pricing_method === 'ACTUAL' && !formData.contract_price) {
      alert('Contract price is required for the Actual Price method.');
      return;
    }
    if (formData.pricing_method === 'COST_MARKUP' && !formData.markup_percent) {
      alert('Markup % is required for the Cost + Markup method.');
      return;
    }

    const payload: Partial<ContractPricing> = {
      debtor: formData.debtor.trim() as unknown as number,
      pricing_method: formData.pricing_method,
      discount_percent: formData.discount_percent ? Number(formData.discount_percent) : 0,
      is_fixed_pricing: formData.is_fixed_pricing,
      valid_from: formData.valid_from || null,
      valid_until: formData.valid_until || null,
      stock_item: formData.scope === 'stock_item' ? formData.stock_item.trim() : null,
      department: formData.scope === 'department' ? (Number(formData.department) as any) : null,
      supplier: formData.scope === 'supplier' ? (Number(formData.supplier) as any) : null,
    };
    if (formData.pricing_method === 'ACTUAL') {
      payload.contract_price = Number(formData.contract_price);
    } else {
      payload.markup_percent = Number(formData.markup_percent);
    }

    mutation.mutate(payload);
  };

  const filteredContracts = contracts.filter((c: ContractPricing) => {
    const value = `${c.debtor} ${c.stock_item ?? ''}`.toLowerCase();
    return value.includes(searchTerm.toLowerCase());
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="flex items-center gap-2 text-blue-600 hover:text-blue-800">
          <ArrowLeft className="w-4 h-4" />
          Back to Menu
        </button>
        <h2 className="text-2xl font-bold text-gray-900">Contract Pricing</h2>
        <button
          onClick={handleNew}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          New Contract Price
        </button>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingId ? 'Edit Contract Price' : 'Create Contract Price'}
          </h3>

          <div className="mb-4 flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                checked={formData.scope === 'stock_item'}
                onChange={() => setFormData({ ...formData, scope: 'stock_item' })}
              />
              Item-specific
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                checked={formData.scope === 'department'}
                onChange={() => setFormData({ ...formData, scope: 'department' })}
              />
              Department-based
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                checked={formData.scope === 'supplier'}
                onChange={() => setFormData({ ...formData, scope: 'supplier' })}
              />
              Supplier-based
            </label>
          </div>

          <form onSubmit={handleSubmit} className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Debtor Account Number *</label>
              <input
                type="text"
                value={formData.debtor}
                onChange={(e) => setFormData({ ...formData, debtor: e.target.value })}
                placeholder="Debtor account number"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              />
            </div>

            {formData.scope === 'stock_item' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stock Code *</label>
                <input
                  type="text"
                  value={formData.stock_item}
                  onChange={(e) => setFormData({ ...formData, stock_item: e.target.value })}
                  placeholder="Stock code"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>
            )}
            {formData.scope === 'department' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Department Number *</label>
                <input
                  type="number"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  placeholder="Department number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>
            )}
            {formData.scope === 'supplier' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Supplier Number *</label>
                <input
                  type="number"
                  value={formData.supplier}
                  onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                  placeholder="Supplier account number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Pricing Method *</label>
              <select
                value={formData.pricing_method}
                onChange={(e) => setFormData({ ...formData, pricing_method: e.target.value as 'ACTUAL' | 'COST_MARKUP' })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="ACTUAL">Actual Price</option>
                <option value="COST_MARKUP">Cost + Markup %</option>
              </select>
            </div>

            {formData.pricing_method === 'ACTUAL' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contract Price *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.contract_price}
                  onChange={(e) => setFormData({ ...formData, contract_price: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Markup % *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.markup_percent}
                  onChange={(e) => setFormData({ ...formData, markup_percent: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Discount %</label>
              <input
                type="number"
                step="0.01"
                value={formData.discount_percent}
                onChange={(e) => setFormData({ ...formData, discount_percent: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_fixed_pricing}
                  onChange={(e) => setFormData({ ...formData, is_fixed_pricing: e.target.checked })}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium">Fixed Pricing (POS cannot discount further)</span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Valid From</label>
              <input
                type="date"
                value={formData.valid_from}
                onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Valid Until</label>
              <input
                type="date"
                value={formData.valid_until}
                onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div className="md:col-span-2 flex gap-3">
              <button
                type="submit"
                disabled={mutation.isPending}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {mutation.isPending ? 'Saving...' : editingId ? 'Update Contract Price' : 'Create Contract Price'}
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

      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search by debtor or stock code..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
        />
      </div>

      <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
        <table className="w-full">
          <thead className="border-b border-gray-200 bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Debtor</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Scope</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Method</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Price / Markup</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Valid</th>
              <th className="px-6 py-3 text-right text-sm font-semibold text-gray-900">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {isLoading ? (
              <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500">Loading...</td></tr>
            ) : error ? (
              <tr><td colSpan={6} className="px-6 py-4 text-center text-red-500">Error loading contract prices</td></tr>
            ) : filteredContracts.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500">No contract prices found</td></tr>
            ) : (
              filteredContracts.map((c: ContractPricing) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{c.debtor}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {c.stock_item ?? (c.department ? `Dept ${c.department}` : c.supplier ? `Supplier ${c.supplier}` : '-')}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{c.pricing_method === 'ACTUAL' ? 'Actual' : 'Cost + Markup'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {c.pricing_method === 'ACTUAL' ? `R ${Number(c.contract_price ?? 0).toFixed(2)}` : `${c.markup_percent}%`}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {c.valid_from || '-'} to {c.valid_until || 'open'}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button onClick={() => handleEdit(c)} className="text-blue-600 hover:text-blue-800">
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button onClick={() => deleteMutation.mutate(c.id)} className="text-red-600 hover:text-red-800">
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

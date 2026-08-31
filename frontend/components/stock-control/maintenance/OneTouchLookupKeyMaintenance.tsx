'use client';

import { useState } from 'react';
import { ArrowLeft, Plus, Edit2, Trash2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import type { OneTouchLookupKey } from '@/lib/types/stockControl';

interface OneTouchLookupKeyMaintenanceProps {
  onBack: () => void;
}

export default function OneTouchLookupKeyMaintenance({ onBack }: OneTouchLookupKeyMaintenanceProps) {
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [keyCharacter, setKeyCharacter] = useState('');
  const [stockCode, setStockCode] = useState('');
  const queryClient = useQueryClient();

  const { data: keys = [], isLoading, error } = useQuery({
    queryKey: ['lookup-keys'],
    queryFn: async () => {
      const result = await stockControlApi.lookupKeys.list();
      return result.results ?? (result as unknown as OneTouchLookupKey[]);
    },
  });

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = { key_character: keyCharacter.toUpperCase(), stock_item: stockCode.trim() };
      if (editingId) {
        return stockControlApi.lookupKeys.update(editingId, payload);
      }
      return stockControlApi.lookupKeys.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lookup-keys'] });
      resetForm();
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
    mutationFn: (id: number) => stockControlApi.lookupKeys.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lookup-keys'] });
    },
  });

  const resetForm = () => {
    setShowForm(false);
    setEditingId(null);
    setKeyCharacter('');
    setStockCode('');
  };

  const handleEdit = (key: OneTouchLookupKey) => {
    setEditingId(key.id);
    setKeyCharacter(key.key_character);
    setStockCode(key.stock_item);
    setShowForm(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!/^[A-Z]$/.test(keyCharacter.toUpperCase())) {
      alert('Key must be a single letter A-Z.');
      return;
    }
    if (!stockCode.trim()) {
      alert('Stock code is required.');
      return;
    }
    mutation.mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="flex items-center gap-2 text-blue-600 hover:text-blue-800">
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <h2 className="text-2xl font-bold text-gray-900">One-Touch Look-Up Keys</h2>
        <button
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          New Key
        </button>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
        Link a single letter (A-Z) to a stock code for fast POS access — press Shift + the letter
        instead of searching, and the linked item's details are pulled in automatically.
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingId ? 'Edit Look-Up Key' : 'New Look-Up Key'}
          </h3>
          <form onSubmit={handleSubmit} className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Key (A-Z) *</label>
              <input
                type="text"
                maxLength={1}
                value={keyCharacter}
                onChange={(e) => setKeyCharacter(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg uppercase"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stock Code *</label>
              <input
                type="text"
                value={stockCode}
                onChange={(e) => setStockCode(e.target.value)}
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
                {mutation.isPending ? 'Saving...' : editingId ? 'Update Key' : 'Create Key'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
        <table className="w-full">
          <thead className="border-b border-gray-200 bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Key</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Stock Code</th>
              <th className="px-6 py-3 text-right text-sm font-semibold text-gray-900">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {isLoading ? (
              <tr><td colSpan={3} className="px-6 py-4 text-center text-gray-500">Loading...</td></tr>
            ) : error ? (
              <tr><td colSpan={3} className="px-6 py-4 text-center text-red-500">Error loading keys</td></tr>
            ) : keys.length === 0 ? (
              <tr><td colSpan={3} className="px-6 py-4 text-center text-gray-500">No look-up keys set up yet</td></tr>
            ) : (
              [...keys].sort((a, b) => a.key_character.localeCompare(b.key_character)).map((key) => (
                <tr key={key.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-lg font-mono font-bold text-gray-900">{key.key_character}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{key.stock_item}</td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button onClick={() => handleEdit(key)} className="text-blue-600 hover:text-blue-800">
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button onClick={() => deleteMutation.mutate(key.id)} className="text-red-600 hover:text-red-800">
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

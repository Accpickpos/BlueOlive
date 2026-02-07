'use client';

import React, { useState, useEffect } from 'react';
import { 
  Supplier, 
  OutstandingBalance, 
  OutstandingBalanceCaptureData,
  useCreditorsAPI 
} from '@/lib/creditorsApi';

interface OutstandingBalanceFormProps {
  suppliers: Supplier[];
  balance?: OutstandingBalance;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function OutstandingBalanceForm({
  suppliers,
  balance,
  onSuccess,
  onCancel,
}: OutstandingBalanceFormProps) {
  const api = useCreditorsAPI();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<OutstandingBalanceCaptureData>({
    supplier_account_number: balance?.supplier_id || 0,
    capture_date: balance?.capture_date || new Date().toISOString().split('T')[0],
    balance_current: balance?.balance_current || 0,
    balance_30_days: balance?.balance_30_days || 0,
    balance_60_days: balance?.balance_60_days || 0,
    balance_90_days: balance?.balance_90_days || 0,
    balance_120_days: balance?.balance_120_days || 0,
    balance_150_days: balance?.balance_150_days || 0,
    balance_180_days: balance?.balance_180_days || 0,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: name.includes('balance') ? parseFloat(value) || 0 : value,
    }));
  };

  const totalBalance = Object.entries(formData).reduce((sum, [key, value]) => {
    if (key.startsWith('balance_')) {
      return sum + (typeof value === 'number' ? value : 0);
    }
    return sum;
  }, 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      console.log('Submitting outstanding balance:', formData);
      
      if (balance?.id) {
        await api.updateOutstandingBalance(balance.id, formData);
        console.log('Outstanding balance updated successfully');
      } else {
        await api.captureOutstandingBalance(formData);
        console.log('Outstanding balance captured successfully');
      }
      
      onSuccess();
    } catch (err: any) {
      console.error('Failed to save outstanding balance:', err);
      setError(err.message || 'Failed to save outstanding balance');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Supplier Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Supplier *
          </label>
          <select
            name="supplier_account_number"
            value={formData.supplier_account_number}
            onChange={handleChange}
            required
            disabled={!!balance}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          >
            <option value="">Select a supplier</option>
            {suppliers.map(supplier => (
              <option key={supplier.account_number} value={supplier.account_number}>
                {supplier.account_number} - {supplier.name}
              </option>
            ))}
          </select>
        </div>

        {/* Capture Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Capture Date *
          </label>
          <input
            type="date"
            name="capture_date"
            value={formData.capture_date}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Balance Fields */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Balance by Age</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Current
            </label>
            <input
              type="number"
              name="balance_current"
              value={formData.balance_current}
              onChange={handleChange}
              step="0.01"
              className="w-full px-2 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              30 Days
            </label>
            <input
              type="number"
              name="balance_30_days"
              value={formData.balance_30_days}
              onChange={handleChange}
              step="0.01"
              className="w-full px-2 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              60 Days
            </label>
            <input
              type="number"
              name="balance_60_days"
              value={formData.balance_60_days}
              onChange={handleChange}
              step="0.01"
              className="w-full px-2 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              90 Days
            </label>
            <input
              type="number"
              name="balance_90_days"
              value={formData.balance_90_days}
              onChange={handleChange}
              step="0.01"
              className="w-full px-2 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              120 Days
            </label>
            <input
              type="number"
              name="balance_120_days"
              value={formData.balance_120_days}
              onChange={handleChange}
              step="0.01"
              className="w-full px-2 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              150 Days
            </label>
            <input
              type="number"
              name="balance_150_days"
              value={formData.balance_150_days}
              onChange={handleChange}
              step="0.01"
              className="w-full px-2 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              180 Days
            </label>
            <input
              type="number"
              name="balance_180_days"
              value={formData.balance_180_days}
              onChange={handleChange}
              step="0.01"
              className="w-full px-2 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Total Balance
            </label>
            <div className="px-2 py-2 border border-gray-300 rounded text-sm font-semibold text-gray-900 bg-white">
              R{totalBalance.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex gap-2 pt-4 border-t">
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Saving...' : balance ? 'Update Balance' : 'Capture Balance'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

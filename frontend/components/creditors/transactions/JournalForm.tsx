'use client';

import { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';

interface JournalFormProps {
  onComplete: () => void;
}

export default function JournalForm({ onComplete }: JournalFormProps) {
  const [formData, setFormData] = useState({
    supplier: '',
    journal_type: 'DEBIT',
    journal_date: new Date().toISOString().split('T')[0],
    journal_number: '',
    amount: 0,
    age_period: 0,
    additional_reference: '',
  });

  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const agePeriods = [
    { value: 0, label: 'Current' },
    { value: 1, label: '30 Days' },
    { value: 2, label: '60 Days' },
    { value: 3, label: '90 Days' },
    { value: 4, label: '120 Days' },
    { value: 5, label: '150 Days' },
    { value: 6, label: '180+ Days' },
  ];

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const fetchSuppliers = async () => {
    try {
      const response = await fetch('/api/creditors/suppliers/');
      if (response.ok) {
        const data = await response.json();
        setSuppliers(data.results || data);
      }
    } catch (err) {
      console.error('Error fetching suppliers:', err);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'number' ? (name === 'age_period' ? parseInt(value) : parseFloat(value)) : value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (!formData.supplier) {
        throw new Error('Please select a supplier');
      }

      if (formData.amount <= 0) {
        throw new Error('Please enter a valid journal amount');
      }

      const payload = {
        ...formData,
        amount: parseFloat(formData.amount.toString()),
      };

      const response = await fetch('/api/creditors/transactions/journal_entry/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create journal entry');
      }

      setSuccess('Journal entry recorded successfully!');
      setTimeout(() => onComplete(), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl">
      <h2 className="text-2xl font-bold mb-2">Journal Entries</h2>
      <p className="text-gray-600 mb-6">Debit Journal - Reduce amount owing to Supplier | Credit Journal - Increase amount owing to Supplier</p>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded">
          <p className="text-green-800">{success}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Supplier Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Supplier *
          </label>
          <select
            name="supplier"
            value={formData.supplier}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select Supplier</option>
            {suppliers.map((s: any) => (
              <option key={s.id} value={s.account_number}>
                {s.name} ({s.account_number})
              </option>
            ))}
          </select>
        </div>

        {/* Journal Type */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Journal Type *
            </label>
            <select
              name="journal_type"
              value={formData.journal_type}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="DEBIT">Debit Journal (Reduce Balance)</option>
              <option value="CREDIT">Credit Journal (Increase Balance)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Journal Date *
            </label>
            <input
              type="date"
              name="journal_date"
              value={formData.journal_date}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Journal Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Journal Number
            </label>
            <input
              type="text"
              name="journal_number"
              value={formData.journal_number}
              onChange={handleInputChange}
              placeholder="Auto-generated if left blank"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Journal Amount *
            </label>
            <input
              type="number"
              name="amount"
              value={formData.amount}
              onChange={handleInputChange}
              required
              placeholder="0.00"
              step="0.01"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Age Period */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Age Period (For Open Item Accounts)
          </label>
          <select
            name="age_period"
            value={formData.age_period}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {agePeriods.map((period) => (
              <option key={period.value} value={period.value}>
                {period.label}
              </option>
            ))}
          </select>
        </div>

        {/* Additional Reference */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Additional Reference / Explanation *
          </label>
          <textarea
            name="additional_reference"
            value={formData.additional_reference}
            onChange={handleInputChange}
            rows={4}
            required
            placeholder="Enter the reason for this journal entry"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Summary */}
        <div className="border-t pt-6 bg-indigo-50 p-4 rounded-lg">
          <h3 className="font-semibold text-gray-900 mb-3">Journal Summary</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Type:</span>
              <span className="font-medium">
                {formData.journal_type === 'DEBIT' ? 'Debit (Reduce Balance)' : 'Credit (Increase Balance)'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Amount:</span>
              <span className="font-medium">R {formData.amount.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Age Period:</span>
              <span className="font-medium">
                {agePeriods.find((p) => p.value === formData.age_period)?.label}
              </span>
            </div>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-4 pt-6 border-t">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition-colors"
          >
            {loading ? 'Processing...' : 'Record Journal Entry'}
          </button>
          <button
            type="button"
            onClick={onComplete}
            className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-900 font-bold py-2 px-4 rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

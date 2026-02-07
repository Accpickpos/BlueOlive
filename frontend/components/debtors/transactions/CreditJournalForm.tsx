'use client';

import { useState } from 'react';
import { apiRequest } from '@/lib/api';

interface CreditJournalData {
  debtor_id: number;
  transaction_number: string;
  transaction_date: string;
  amount: string;
  vat_amount: string;
  reference: string;
  additional_reference: string;
}

export default function CreditJournalForm() {
  const [formData, setFormData] = useState<CreditJournalData>({
    debtor_id: 0,
    transaction_number: '',
    transaction_date: new Date().toISOString().split('T')[0],
    amount: '',
    vat_amount: '0',
    reference: '',
    additional_reference: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (!formData.debtor_id || !formData.transaction_number || !formData.amount) {
        setError('Please fill in all required fields');
        setLoading(false);
        return;
      }

      const response = await apiRequest(
        '/api/debtors/transactions/',
        {
          method: 'POST',
          body: {
            ...formData,
            transaction_type: 'CRJ',
            debtor_id: parseInt(formData.debtor_id.toString()),
            amount: parseFloat(formData.amount),
            vat_amount: parseFloat(formData.vat_amount || '0'),
          }
        }
      );

      setSuccess(`Credit Journal #${formData.transaction_number} posted successfully`);
      setFormData({
        debtor_id: 0,
        transaction_number: '',
        transaction_date: new Date().toISOString().split('T')[0],
        amount: '',
        vat_amount: '0',
        reference: '',
        additional_reference: '',
      });
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to post credit journal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">
          {success}
        </div>
      )}

      {/* Debtor Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Debtor <span className="text-red-500">*</span>
        </label>
        <input
          type="number"
          name="debtor_id"
          value={formData.debtor_id}
          onChange={handleChange}
          placeholder="Enter Debtor ID"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Transaction Number */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Journal Number <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          name="transaction_number"
          value={formData.transaction_number}
          onChange={handleChange}
          placeholder="e.g., CRJ001"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Transaction Date */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Journal Date <span className="text-red-500">*</span>
        </label>
        <input
          type="date"
          name="transaction_date"
          value={formData.transaction_date}
          onChange={handleChange}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Amount Fields */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Amount (ex VAT) <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            name="amount"
            step="0.01"
            value={formData.amount}
            onChange={handleChange}
            placeholder="0.00"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            VAT Amount
          </label>
          <input
            type="number"
            name="vat_amount"
            step="0.01"
            value={formData.vat_amount}
            onChange={handleChange}
            placeholder="0.00"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Reference Fields */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Reference
        </label>
        <input
          type="text"
          name="reference"
          value={formData.reference}
          onChange={handleChange}
          placeholder="e.g., Credit Note #CN123"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Additional Reference
        </label>
        <textarea
          name="additional_reference"
          value={formData.additional_reference}
          onChange={handleChange}
          placeholder="Additional notes or reference information"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Submit Button */}
      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Posting...' : 'Post Credit Journal'}
        </button>
      </div>
    </form>
  );
}

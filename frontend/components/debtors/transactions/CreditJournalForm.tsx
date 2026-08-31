'use client';

import { useState, useEffect } from 'react';
import debtorsApi from '@/lib/debtorsApi';
import { getApiErrorMessage } from '@/lib/api';

interface DebtorOption {
  id: number;
  name: string;
  acctype: string;
}

// Debtopen.AGEING_CHOICES — manual §2.2 "Credit Journal for Open Item
// Debtors": "The total value of the journal may only be allocated to ONE
// ageing period."
const AGE_PERIODS = [
  { value: '0', label: 'Current' },
  { value: '1', label: '30 Days' },
  { value: '2', label: '60 Days' },
  { value: '3', label: '90 Days' },
  { value: '4', label: '120+ Days' },
];

interface CreditJournalData {
  debtor_id: number;
  transaction_date: string;
  amount: string;
  reference: string;
  additional_reference: string;
  age_period: string;
}

export default function CreditJournalForm() {
  const [formData, setFormData] = useState<CreditJournalData>({
    debtor_id: 0,
    transaction_date: new Date().toISOString().split('T')[0],
    amount: '',
    reference: '',
    additional_reference: '',
    age_period: '0',
  });

  const [debtors, setDebtors] = useState<DebtorOption[]>([]);
  const [loadingDebtors, setLoadingDebtors] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    debtorsApi.accounts
      .list()
      .then((response) => {
        setDebtors(
          (response.results || []).map((d: any) => ({
            id: d.id,
            name: d.name,
            acctype: d.account_type ?? d.acctype ?? '',
          }))
        );
      })
      .catch(() => console.error('Failed to load debtors'))
      .finally(() => setLoadingDebtors(false));
  }, []);

  const selectedDebtor = debtors.find((d) => d.id === formData.debtor_id) || null;
  const isOpenItem = selectedDebtor?.acctype === 'O';

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'debtor_id' ? parseInt(value) || 0 : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (!formData.debtor_id || !formData.amount || !formData.reference.trim()) {
        setError('Please fill in all required fields, including a reference motivating the journal');
        setLoading(false);
        return;
      }

      const description = formData.additional_reference
        ? `${formData.reference} - ${formData.additional_reference}`
        : formData.reference;

      await debtorsApi.transactions.postCredit({
        debtor_id: formData.debtor_id,
        amount: parseFloat(formData.amount),
        description,
        transaction_date: formData.transaction_date,
        ...(isOpenItem ? { age_period: formData.age_period } : {}),
      });

      setSuccess('Credit Journal posted successfully');
      setFormData({
        debtor_id: 0,
        transaction_date: new Date().toISOString().split('T')[0],
        amount: '',
        reference: '',
        additional_reference: '',
        age_period: '0',
      });
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to post credit journal'));
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
        <select
          name="debtor_id"
          value={formData.debtor_id}
          onChange={handleChange}
          disabled={loadingDebtors}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
        >
          <option value="">Select a debtor...</option>
          {debtors.map(debtor => (
            <option key={debtor.id} value={debtor.id}>
              {debtor.name}
            </option>
          ))}
        </select>
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

      {/* Amount */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Journal Amount <span className="text-red-500">*</span>
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

      {/* Ageing Period — Open Item debtors only */}
      {isOpenItem && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Allocate to Ageing Period <span className="text-red-500">*</span>
          </label>
          <select
            name="age_period"
            value={formData.age_period}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {AGE_PERIODS.map(period => (
              <option key={period.value} value={period.value}>{period.label}</option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Open Item accounts: the full journal amount may only be allocated to ONE ageing period.
          </p>
        </div>
      )}

      {/* Reference Fields */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Additional Reference <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          name="reference"
          value={formData.reference}
          onChange={handleChange}
          placeholder="Short explanation motivating the journal — appears on the Debtor's Statement"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Notes
        </label>
        <textarea
          name="additional_reference"
          value={formData.additional_reference}
          onChange={handleChange}
          placeholder="Additional notes (optional)"
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

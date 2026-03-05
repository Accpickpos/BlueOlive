'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

interface InterestData {
  debtor_id: number;
  interest_rate: string;
  calculation_date: string;
  reference: string;
}

interface DebtorBalance {
  id: number;
  name: string;
  current_balance: number;
}

export default function InterestChargingForm() {
  const [formData, setFormData] = useState<InterestData>({
    debtor_id: 0,
    interest_rate: '10.5',
    calculation_date: new Date().toISOString().split('T')[0],
    reference: '',
  });

  const [debtors, setDebtors] = useState<DebtorBalance[]>([]);
  const [selectedDebtor, setSelectedDebtor] = useState<DebtorBalance | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loadingDebtors, setLoadingDebtors] = useState(true);

  useEffect(() => {
    loadDebtors();
  }, []);

  const loadDebtors = async () => {
    try {
      const response = await apiRequest('/api/v1/debtors/');
      if ((response as any).results) {
        setDebtors((response as any).results);
      }
    } catch (err) {
      console.error('Failed to load debtors');
    } finally {
      setLoadingDebtors(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    if (name === 'debtor_id') {
      const debtor = debtors.find(d => d.id === parseInt(value));
      setSelectedDebtor(debtor || null);
    }
  };

  const calculateInterest = () => {
    if (!selectedDebtor || !formData.interest_rate) {
      return 0;
    }
    const balance = Math.max(0, selectedDebtor.current_balance);
    const rate = parseFloat(formData.interest_rate) || 0;
    return (balance * rate) / 100;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (!formData.debtor_id || !formData.interest_rate) {
        setError('Please fill in all required fields');
        setLoading(false);
        return;
      }

      const interestAmount = calculateInterest();
      
      const response = await apiRequest(
        '/api/v1/debtors/transactions/',
        {
          method: 'POST',
          body: {
            debtor_id: parseInt(formData.debtor_id.toString()),
            transaction_type: 'INT',
            transaction_number: `INT-${new Date().getTime()}`,
            transaction_date: formData.calculation_date,
            amount: interestAmount,
            vat_amount: 0,
            reference: formData.reference || `Interest charge @ ${formData.interest_rate}%`,
            additional_reference: `Interest charge calculated on balance of R${selectedDebtor?.current_balance.toFixed(2)}`,
          }
        }
      );

      setSuccess(`Interest charge of R${interestAmount.toFixed(2)} posted successfully`);
      setFormData({
        debtor_id: 0,
        interest_rate: '10.5',
        calculation_date: new Date().toISOString().split('T')[0],
        reference: '',
      });
      setSelectedDebtor(null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to charge interest');
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
              {debtor.name} (Balance: R{debtor.current_balance.toFixed(2)})
            </option>
          ))}
        </select>
      </div>

      {/* Current Balance Display */}
      {selectedDebtor && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-gray-700">
            <span className="font-medium">Current Balance:</span> R{selectedDebtor.current_balance.toFixed(2)}
          </p>
        </div>
      )}

      {/* Interest Rate */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Interest Rate (%) <span className="text-red-500">*</span>
        </label>
        <input
          type="number"
          name="interest_rate"
          step="0.01"
          value={formData.interest_rate}
          onChange={handleChange}
          placeholder="10.5"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-500 mt-1">Monthly or annual interest rate to apply</p>
      </div>

      {/* Calculated Interest */}
      {selectedDebtor && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-lg font-semibold text-green-700">
            Interest to Charge: R{calculateInterest().toFixed(2)}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            Based on balance of R{selectedDebtor.current_balance.toFixed(2)} at {formData.interest_rate}%
          </p>
        </div>
      )}

      {/* Calculation Date */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Calculation Date
        </label>
        <input
          type="date"
          name="calculation_date"
          value={formData.calculation_date}
          onChange={handleChange}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Reference */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Reference / Notes
        </label>
        <input
          type="text"
          name="reference"
          value={formData.reference}
          onChange={handleChange}
          placeholder="e.g., Monthly interest charge"
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
          {loading ? 'Charging Interest...' : 'Charge Interest'}
        </button>
      </div>
    </form>
  );
}

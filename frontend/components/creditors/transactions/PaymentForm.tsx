'use client';

import { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';

interface PaymentFormProps {
  onComplete: () => void;
}

export default function PaymentForm({ onComplete }: PaymentFormProps) {
  const [formData, setFormData] = useState({
    supplier: '',
    payment_date: new Date().toISOString().split('T')[0],
    amount_paid: 0,
    settlement_discount: 0,
    payment_reference: '',
    additional_reference: '',
  });

  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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
      [name]: type === 'number' ? parseFloat(value) : value,
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

      if (formData.amount_paid <= 0) {
        throw new Error('Please enter a valid payment amount');
      }

      const payload = {
        ...formData,
        amount_paid: parseFloat(formData.amount_paid.toString()),
        settlement_discount: parseFloat(formData.settlement_discount.toString()),
      };

      const response = await fetch('/api/creditors/transactions/payment/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create payment');
      }

      setSuccess('Payment recorded successfully!');
      setTimeout(() => onComplete(), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl">
      <h2 className="text-2xl font-bold mb-2">Post Payment(s)</h2>
      <p className="text-gray-600 mb-6">Record supplier payments</p>

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
        {/* Header Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Payment Date *
            </label>
            <input
              type="date"
              name="payment_date"
              value={formData.payment_date}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount Paid *
            </label>
            <input
              type="number"
              name="amount_paid"
              value={formData.amount_paid}
              onChange={handleInputChange}
              required
              placeholder="0.00"
              step="0.01"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Settlement Discount
            </label>
            <input
              type="number"
              name="settlement_discount"
              value={formData.settlement_discount}
              onChange={handleInputChange}
              placeholder="0.00"
              step="0.01"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* References */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Payment Reference
          </label>
          <input
            type="text"
            name="payment_reference"
            value={formData.payment_reference}
            onChange={handleInputChange}
            placeholder="E.g. Cheque #, Transfer Ref"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Additional Reference
          </label>
          <textarea
            name="additional_reference"
            value={formData.additional_reference}
            onChange={handleInputChange}
            rows={3}
            placeholder="Any additional information"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Summary */}
        <div className="border-t pt-6 bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold text-gray-900 mb-3">Payment Summary</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Amount Paid:</span>
              <span className="font-medium">R {formData.amount_paid.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Settlement Discount:</span>
              <span className="font-medium">R {formData.settlement_discount.toFixed(2)}</span>
            </div>
            <div className="flex justify-between border-t pt-2 mt-2">
              <span className="text-gray-700 font-semibold">Total Payment:</span>
              <span className="font-bold text-lg">
                R {(formData.amount_paid + formData.settlement_discount).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-4 pt-6 border-t">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition-colors"
          >
            {loading ? 'Processing...' : 'Record Payment'}
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

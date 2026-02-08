'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

interface ReceiptRecord {
  id: string;
  debtor_id: number;
  debtor_name: string;
  amount: string;
  reference: string;
}

interface BatchReceiptData {
  batch_reference: string;
  posting_date: string;
  receipts: ReceiptRecord[];
}

export default function BatchReceiptPostingForm() {
  const [formData, setFormData] = useState<BatchReceiptData>({
    batch_reference: '',
    posting_date: new Date().toISOString().split('T')[0],
    receipts: [{ id: '1', debtor_id: 0, debtor_name: '', amount: '', reference: '' }],
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [debtors, setDebtors] = useState<any[]>([]);
  const [loadingDebtors, setLoadingDebtors] = useState(true);

  useEffect(() => {
    loadDebtors();
  }, []);

  const loadDebtors = async () => {
    try {
      const response = await apiRequest('/api/debtors/');
      if ((response as any).results) {
        setDebtors((response as any).results);
      }
    } catch (err) {
      console.error('Failed to load debtors');
    } finally {
      setLoadingDebtors(false);
    }
  };

  const handleBatchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleReceiptChange = (id: string, field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      receipts: prev.receipts.map(receipt => 
        receipt.id === id
          ? { 
              ...receipt, 
              [field]: value,
              debtor_name: field === 'debtor_id' 
                ? (debtors.find(d => d.id === parseInt(value))?.name || '')
                : receipt.debtor_name
            }
          : receipt
      )
    }));
  };

  const addReceipt = () => {
    const newId = Math.max(...formData.receipts.map(r => parseInt(r.id)), 0) + 1;
    setFormData(prev => ({
      ...prev,
      receipts: [
        ...prev.receipts,
        { id: newId.toString(), debtor_id: 0, debtor_name: '', amount: '', reference: '' }
      ]
    }));
  };

  const removeReceipt = (id: string) => {
    if (formData.receipts.length > 1) {
      setFormData(prev => ({
        ...prev,
        receipts: prev.receipts.filter(receipt => receipt.id !== id)
      }));
    }
  };

  const getTotalAmount = () => {
    return formData.receipts.reduce((sum, receipt) => sum + (parseFloat(receipt.amount) || 0), 0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (!formData.batch_reference) {
        setError('Batch reference is required');
        setLoading(false);
        return;
      }

      const validReceipts = formData.receipts.filter(r => r.debtor_id && r.amount);
      if (validReceipts.length === 0) {
        setError('Please add at least one receipt with debtor and amount');
        setLoading(false);
        return;
      }

      const transactionPromises = validReceipts.map(receipt =>
        apiRequest('/api/debtors/transactions/', {
          method: 'POST',
          body: {
            debtor_id: receipt.debtor_id,
            transaction_type: 'RCT',
            transaction_number: receipt.reference || `RCT-${formData.batch_reference}-${receipt.id}`,
            transaction_date: formData.posting_date,
            amount: parseFloat(receipt.amount),
            vat_amount: 0,
            reference: `Batch: ${formData.batch_reference}`,
            additional_reference: receipt.reference,
          }
        })
      );

      await Promise.all(transactionPromises);

      setSuccess(`Batch ${formData.batch_reference} posted successfully with ${validReceipts.length} receipts (Total: R${getTotalAmount().toFixed(2)})`);
      setFormData({
        batch_reference: '',
        posting_date: new Date().toISOString().split('T')[0],
        receipts: [{ id: '1', debtor_id: 0, debtor_name: '', amount: '', reference: '' }],
      });
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to post batch receipts');
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

      {/* Batch Header */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Batch Reference <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="batch_reference"
            value={formData.batch_reference}
            onChange={handleBatchChange}
            placeholder="e.g., BATCH-2024-001"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Posting Date
          </label>
          <input
            type="date"
            name="posting_date"
            value={formData.posting_date}
            onChange={handleBatchChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Receipts Table */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-medium text-gray-700">Debtor</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Amount</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Reference</th>
                <th className="px-4 py-3 text-center font-medium text-gray-700">Action</th>
              </tr>
            </thead>
            <tbody>
              {formData.receipts.map((receipt) => (
                <tr key={receipt.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <select
                      value={receipt.debtor_id}
                      onChange={(e) => handleReceiptChange(receipt.id, 'debtor_id', e.target.value)}
                      disabled={loadingDebtors}
                      className="w-full px-3 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
                    >
                      <option value="">Select...</option>
                      {debtors.map(debtor => (
                        <option key={debtor.id} value={debtor.id}>
                          {debtor.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      step="0.01"
                      value={receipt.amount}
                      onChange={(e) => handleReceiptChange(receipt.id, 'amount', e.target.value)}
                      placeholder="0.00"
                      className="w-full px-3 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      value={receipt.reference}
                      onChange={(e) => handleReceiptChange(receipt.id, 'reference', e.target.value)}
                      placeholder="e.g., Cheque #123"
                      className="w-full px-3 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      type="button"
                      onClick={() => removeReceipt(receipt.id)}
                      className="text-red-600 hover:text-red-900 text-sm font-medium"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Total Row */}
        <div className="bg-gray-50 border-t border-gray-200 px-4 py-3 flex justify-between items-center">
          <div>
            <button
              type="button"
              onClick={addReceipt}
              className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-900 hover:bg-blue-50 rounded border border-blue-200"
            >
              + Add Receipt
            </button>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Total Amount:</p>
            <p className="text-lg font-bold text-gray-900">R{getTotalAmount().toFixed(2)}</p>
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Posting Batch...' : 'Post Batch Receipts'}
        </button>
      </div>
    </form>
  );
}

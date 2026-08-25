'use client';

import { useState, useEffect } from 'react';
import { Plus, AlertCircle, CheckCircle2 } from 'lucide-react';
import cashBookApi from '@/lib/cashBookApi';
import { getApiErrorMessage } from '@/lib/api';
import { BankReconciliation } from '@/lib/types/cashBook';
import { ReconciliationStatus, BalanceCard } from '@/components/cash-book';

export default function BankReconciliationPage() {
  const [reconciliations, setReconciliations] = useState<BankReconciliation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showForm, setShowForm] = useState(false);

  const [formData, setFormData] = useState({
    reconciliation_date: new Date().toISOString().split('T')[0],
    bank_account_number: '',
    statement_date: new Date().toISOString().split('T')[0],
    statement_number: '',
    opening_balance: 0,
    closing_balance_per_statement: 0,
    closing_balance_per_books: 0,
    notes: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const reconciliationsRes = await cashBookApi.reconciliations.list();
      setReconciliations((reconciliationsRes.results || []) as BankReconciliation[]);
    } catch (err) {
      setError('Failed to load data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value,
    }));
  };

  // Preview only — the backend computes the authoritative difference/is_balanced
  // from closing_balance_per_statement vs closing_balance_per_books.
  const previewDifference = formData.closing_balance_per_statement - formData.closing_balance_per_books;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!formData.reconciliation_date || !formData.bank_account_number || !formData.statement_date) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);

    try {
      await cashBookApi.reconciliations.create(formData);
      setSuccess('Bank reconciliation created successfully!');

      setFormData({
        reconciliation_date: new Date().toISOString().split('T')[0],
        bank_account_number: '',
        statement_date: new Date().toISOString().split('T')[0],
        statement_number: '',
        opening_balance: 0,
        closing_balance_per_statement: 0,
        closing_balance_per_books: 0,
        notes: '',
      });
      setShowForm(false);

      await fetchData();
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to create reconciliation'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Bank Reconciliation</h1>
          <p className="text-gray-600 mt-2">Reconcile bank statements with system balances</p>
        </div>

        {/* Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <p className="text-green-800">{success}</p>
          </div>
        )}

        {/* Reconciliation Form */}
        {showForm && (
          <div className="mb-6 bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
            <h2 className="text-xl font-bold mb-4">New Bank Reconciliation</h2>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Reconciliation Date *</label>
                  <input
                    type="date"
                    name="reconciliation_date"
                    value={formData.reconciliation_date}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Bank Account Number *</label>
                  <input
                    type="text"
                    name="bank_account_number"
                    value={formData.bank_account_number}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Statement Date *</label>
                  <input
                    type="date"
                    name="statement_date"
                    value={formData.statement_date}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Statement Number</label>
                <input
                  type="text"
                  name="statement_number"
                  value={formData.statement_number}
                  onChange={handleInputChange}
                  placeholder="Optional"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Opening Balance *</label>
                  <input
                    type="number"
                    name="opening_balance"
                    value={formData.opening_balance}
                    onChange={handleInputChange}
                    step="0.01"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Closing Balance (Statement) *</label>
                  <input
                    type="number"
                    name="closing_balance_per_statement"
                    value={formData.closing_balance_per_statement}
                    onChange={handleInputChange}
                    step="0.01"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Closing Balance (Books) *</label>
                  <input
                    type="number"
                    name="closing_balance_per_books"
                    value={formData.closing_balance_per_books}
                    onChange={handleInputChange}
                    step="0.01"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <BalanceCard title="Statement Balance" amount={formData.closing_balance_per_statement} variant="balance" padding="p-4" />
                <BalanceCard title="Books Balance" amount={formData.closing_balance_per_books} variant="balance" padding="p-4" />
                <BalanceCard
                  title="Difference (preview)"
                  amount={previewDifference}
                  variant={previewDifference === 0 ? 'income' : 'expense'}
                  padding="p-4"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleInputChange}
                  placeholder="Reconciliation notes, e.g., outstanding items, pending transfers"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
                >
                  {loading ? 'Saving...' : 'Create Reconciliation'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 bg-gray-300 text-gray-900 rounded-lg hover:bg-gray-400 font-medium"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Add Button */}
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="mb-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            New Reconciliation
          </button>
        )}

        {/* Reconciliations List */}
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Loading reconciliations...</p>
          </div>
        ) : reconciliations.length === 0 ? (
          <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-500">No bank reconciliations found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {reconciliations.map((recon) => (
              <div key={recon.id} className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500 hover:shadow-lg transition">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">
                      {new Date(recon.reconciliation_date).toLocaleDateString('en-ZA')}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {recon.reconciliation_number} — {recon.bank_account_number}
                    </p>
                  </div>
                  <ReconciliationStatus
                    status={recon.is_balanced ? 'RECONCILED' : 'VARIANCE'}
                    varianceAmount={recon.difference || 0}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <p className="text-xs text-gray-600 font-semibold">Closing Balance (Statement)</p>
                    <p className="text-2xl font-bold text-blue-900">R{(recon.closing_balance_per_statement || 0).toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 font-semibold">Closing Balance (Books)</p>
                    <p className="text-2xl font-bold text-blue-900">R{(recon.closing_balance_per_books || 0).toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 font-semibold">Difference</p>
                    <p className={`text-2xl font-bold ${recon.is_balanced ? 'text-green-600' : 'text-red-600'}`}>
                      R{Math.abs(recon.difference || 0).toFixed(2)}
                    </p>
                  </div>
                </div>

                {recon.notes && (
                  <div className="mt-4 p-3 bg-gray-50 rounded border border-gray-200">
                    <p className="text-sm text-gray-700">
                      <strong>Notes:</strong> {recon.notes}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

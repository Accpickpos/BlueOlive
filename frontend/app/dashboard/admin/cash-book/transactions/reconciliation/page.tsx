'use client';

import { useState, useEffect } from 'react';
import { Plus, AlertCircle, CheckCircle2, Eye, Check } from 'lucide-react';
import cashBookApi from '@/lib/cashBookApi';
import { BankReconciliation, CashBookTransaction } from '@/lib/types/cashBook';
import { ReconciliationStatus, BalanceCard } from '@/components/cash-book';

interface ReconciliationItem {
  transaction_id?: number;
  description: string;
  amount: number;
  status: 'RECONCILED' | 'OUTSTANDING' | 'CANCELLED';
  date?: string;
}

interface ReconciliationData extends BankReconciliation {
  items?: ReconciliationItem[];
}

export default function BankReconciliationPage() {
  const [reconciliations, setReconciliations] = useState<ReconciliationData[]>([]);
  const [activeReconciliation, setActiveReconciliation] = useState<ReconciliationData | null>(null);
  const [transactions, setTransactions] = useState<CashBookTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showForm, setShowForm] = useState(false);

  const [formData, setFormData] = useState<Partial<ReconciliationData>>({
    reconciliation_date: new Date().toISOString().split('T')[0],
    bank_statement_balance: 0,
    system_balance: 0,
    variance: 0,
    notes: '',
    items: [],
  });

  const [selectedItems, setSelectedItems] = useState<number[]>([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [reconciliationsRes, transactionsRes] = await Promise.all([
        cashBookApi.reconciliations.list(),
        cashBookApi.transactions.list(),
      ]);
      setReconciliations(reconciliationsRes.results || []);
      setTransactions((transactionsRes.results || []) as CashBookTransaction[]);
    } catch (err) {
      setError('Failed to load data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value,
    }));

    // Calculate variance automatically
    if (name === 'bank_statement_balance' || name === 'system_balance') {
      const bankBalance = name === 'bank_statement_balance' ? parseFloat(value) : formData.bank_statement_balance || 0;
      const systemBalance = name === 'system_balance' ? parseFloat(value) : formData.system_balance || 0;
      const variance = Math.abs(bankBalance - systemBalance);
      
      setFormData(prev => ({
        ...prev,
        [name]: type === 'number' ? parseFloat(value) : value,
        variance: variance,
      }));
    }
  };

  const handleToggleItem = (transactionId: number) => {
    setSelectedItems(prev =>
      prev.includes(transactionId)
        ? prev.filter(id => id !== transactionId)
        : [...prev, transactionId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!formData.reconciliation_date || formData.bank_statement_balance === undefined || formData.system_balance === undefined) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);

    try {
      const reconciliationData = {
        reconciliation_date: formData.reconciliation_date,
        bank_statement_balance: formData.bank_statement_balance,
        system_balance: formData.system_balance,
        variance: formData.variance || 0,
        notes: formData.notes,
      };

      const response = await cashBookApi.reconciliations.create(reconciliationData);
      setSuccess('Bank reconciliation created successfully!');

      // Reset form
      setFormData({
        reconciliation_date: new Date().toISOString().split('T')[0],
        bank_statement_balance: 0,
        system_balance: 0,
        variance: 0,
        notes: '',
        items: [],
      });
      setSelectedItems([]);
      setShowForm(false);

      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create reconciliation');
    } finally {
      setLoading(false);
    }
  };

  const outstandingItems = transactions.filter(
    t => t.date && new Date(t.date) <= new Date(formData.reconciliation_date || new Date())
  );

  const reconciliationStatus = formData.variance === 0 ? 'RECONCILED' : (formData.variance! > 0 && formData.variance! < 100 ? 'PENDING' : 'VARIANCE');

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
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reconciliation Date *
                  </label>
                  <input
                    type="date"
                    name="reconciliation_date"
                    value={formData.reconciliation_date || ''}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bank Statement Balance *
                  </label>
                  <input
                    type="number"
                    name="bank_statement_balance"
                    value={formData.bank_statement_balance || 0}
                    onChange={handleInputChange}
                    placeholder="0.00"
                    step="0.01"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    System Balance *
                  </label>
                  <input
                    type="number"
                    name="system_balance"
                    value={formData.system_balance || 0}
                    onChange={handleInputChange}
                    placeholder="0.00"
                    step="0.01"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <BalanceCard
                  title="Bank Balance"
                  amount={formData.bank_statement_balance || 0}
                  variant="balance"
                  padding="p-4"
                />
                <BalanceCard
                  title="System Balance"
                  amount={formData.system_balance || 0}
                  variant="balance"
                  padding="p-4"
                />
                <BalanceCard
                  title="Variance"
                  amount={formData.variance || 0}
                  variant={formData.variance === 0 ? 'income' : 'expense'}
                  padding="p-4"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  name="notes"
                  value={formData.notes || ''}
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

            {/* Outstanding Items Selection */}
            {outstandingItems.length > 0 && (
              <div className="mt-8 pt-8 border-t border-gray-200">
                <h3 className="text-lg font-bold mb-4">Outstanding Items</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {outstandingItems.map(item => (
                    <div
                      key={item.id}
                      className="flex items-center gap-3 p-3 bg-gray-50 rounded border border-gray-200 hover:bg-gray-100"
                    >
                      <input
                        type="checkbox"
                        checked={selectedItems.includes(item.id || 0)}
                        onChange={() => item.id && handleToggleItem(item.id)}
                        className="w-4 h-4 border-gray-300 rounded"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{item.description}</p>
                        <p className="text-xs text-gray-600">
                          {new Date(item.date).toLocaleDateString('en-ZA')} • R{item.amount.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
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
            {reconciliations.map(recon => (
              <div key={recon.id} className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500 hover:shadow-lg transition">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">
                      {new Date(recon.reconciliation_date).toLocaleDateString('en-ZA')}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Reconciliation ID: {recon.id}
                    </p>
                  </div>
                  <ReconciliationStatus
                    status={recon.variance === 0 ? 'RECONCILED' : 'VARIANCE'}
                    varianceAmount={recon.variance}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <p className="text-xs text-gray-600 font-semibold">Bank Statement Balance</p>
                    <p className="text-2xl font-bold text-blue-900">R{recon.bank_statement_balance.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 font-semibold">System Balance</p>
                    <p className="text-2xl font-bold text-blue-900">R{recon.system_balance.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 font-semibold">Variance</p>
                    <p className={`text-2xl font-bold ${recon.variance === 0 ? 'text-green-600' : 'text-red-600'}`}>
                      R{Math.abs(recon.variance).toFixed(2)}
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

                <div className="mt-4 flex gap-2">
                  <button className="px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100 flex items-center gap-1">
                    <Eye className="w-4 h-4" />
                    View Details
                  </button>
                  <button className="px-3 py-1.5 text-sm font-medium text-green-600 bg-green-50 rounded hover:bg-green-100 flex items-center gap-1">
                    <Check className="w-4 h-4" />
                    Mark as Reviewed
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

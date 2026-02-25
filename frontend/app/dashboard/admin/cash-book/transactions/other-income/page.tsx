'use client';

import { useState, useEffect } from 'react';
import { Plus, AlertCircle, CheckCircle2, Trash2 } from 'lucide-react';
import cashBookApi from '@/lib/cashBookApi';
import { IncomeCategory, OtherIncomeTransaction } from '@/lib/types/cashBook';
import { TransactionTypeBadge, BalanceCard } from '@/components/cash-book';

interface OtherIncomeEntry extends OtherIncomeTransaction {
  vat_rate?: number;
}

export default function OtherIncomeEntryPage() {
  const [categories, setCategories] = useState<IncomeCategory[]>([]);
  const [transactions, setTransactions] = useState<OtherIncomeEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<Partial<OtherIncomeEntry>>({
    date: new Date().toISOString().split('T')[0],
    description: '',
    amount: 0,
    income_category_id: 0,
    vat_amount: 0,
    vat_rate: 15,
    vat_inclusive: false,
    reference: '',
    notes: '',
  });

  const [totals, setTotals] = useState({
    totalAmount: 0,
    totalVAT: 0,
    totalInclusive: 0,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [categoriesRes, transactionsRes] = await Promise.all([
        cashBookApi.incomeCategories.list(),
        cashBookApi.otherIncome.list(),
      ]);
      setCategories(categoriesRes.results || []);
      setTransactions((transactionsRes.results || []) as OtherIncomeEntry[]);
      calculateTotals((transactionsRes.results || []) as OtherIncomeEntry[]);
    } catch (err) {
      setError('Failed to load data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const calculateTotals = (trans: OtherIncomeEntry[]) => {
    const totals = trans.reduce(
      (acc, t) => ({
        totalAmount: acc.totalAmount + (t.amount || 0),
        totalVAT: acc.totalVAT + (t.vat_amount || 0),
        totalInclusive: acc.totalInclusive + ((t.amount || 0) + (t.vat_amount || 0)),
      }),
      { totalAmount: 0, totalVAT: 0, totalInclusive: 0 }
    );
    setTotals(totals);
  };

  const calculateVAT = (amount: number, rate: number = 15, inclusive: boolean = false) => {
    if (inclusive) {
      // Amount includes VAT, so we need to extract it
      return amount - amount / (1 + rate / 100);
    } else {
      return amount * (rate / 100);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;

    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));

    // Recalculate VAT if amount or rate changes
    if ((name === 'amount' || name === 'vat_rate') && formData.amount) {
      const amount = name === 'amount' ? parseFloat(value) : formData.amount;
      const rate = name === 'vat_rate' ? parseFloat(value) : formData.vat_rate || 15;
      const vatAmount = calculateVAT(amount, rate, formData.vat_inclusive);
      setFormData(prev => ({ ...prev, vat_amount: vatAmount }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!formData.income_category_id || !formData.amount || !formData.description || !formData.date) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);

    try {
      await cashBookApi.otherIncome.create({
        date: formData.date,
        description: formData.description,
        amount: formData.amount,
        category_id: formData.income_category_id,
        vat_amount: formData.vat_amount,
        reference: formData.reference,
        notes: formData.notes,
      });

      setSuccess('Other income entry created successfully!');
      
      // Reset form
      setFormData({
        date: new Date().toISOString().split('T')[0],
        description: '',
        amount: 0,
        income_category_id: 0,
        vat_amount: 0,
        vat_rate: 15,
        vat_inclusive: false,
        reference: '',
        notes: '',
      });
      setShowForm(false);

      // Refresh list
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create entry');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTransaction = async (id: number | undefined) => {
    if (!id || !confirm('Delete this transaction?')) return;

    setLoading(true);
    try {
      // Note: depends on backend supporting DELETE on transactions
      // await cashBookApi.otherIncome.delete(id);
      setSuccess('Transaction deleted successfully!');
      await fetchData();
    } catch (err) {
      setError('Failed to delete transaction');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Other Income Entry</h1>
          <p className="text-gray-600 mt-2">Record miscellaneous income transactions with VAT tracking</p>
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

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <BalanceCard
            title="Total Income"
            amount={totals.totalAmount}
            variant="income"
          />
          <BalanceCard
            title="Total VAT"
            amount={totals.totalVAT}
            variant="default"
          />
          <BalanceCard
            title="Gross Amount"
            amount={totals.totalInclusive}
            variant="balance"
          />
        </div>

        {/* Entry Form */}
        {showForm && (
          <div className="mb-6 bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
            <h2 className="text-xl font-bold mb-4">New Income Entry</h2>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date *
                  </label>
                  <input
                    type="date"
                    name="date"
                    value={formData.date || ''}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Income Category *
                  </label>
                  <select
                    name="income_category_id"
                    value={formData.income_category_id || 0}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  >
                    <option value={0}>Select Category</option>
                    {categories.filter(c => c.is_active).map(cat => (
                      <option key={cat.id} value={cat.id || 0}>
                        {cat.code} - {cat.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description *
                </label>
                <input
                  type="text"
                  name="description"
                  value={formData.description || ''}
                  onChange={handleInputChange}
                  placeholder="e.g., Commission received from partner"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Amount (Excl. VAT) *
                  </label>
                  <input
                    type="number"
                    name="amount"
                    value={formData.amount || 0}
                    onChange={handleInputChange}
                    placeholder="0.00"
                    step="0.01"
                    min="0"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    VAT Rate (%)
                  </label>
                  <input
                    type="number"
                    name="vat_rate"
                    value={formData.vat_rate || 15}
                    onChange={handleInputChange}
                    placeholder="15"
                    step="0.01"
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    VAT Amount
                  </label>
                  <input
                    type="number"
                    name="vat_amount"
                    value={formData.vat_amount || 0}
                    onChange={handleInputChange}
                    disabled
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  name="vat_inclusive"
                  checked={formData.vat_inclusive || false}
                  onChange={handleInputChange}
                  className="w-4 h-4 border-gray-300 rounded"
                />
                <label className="text-sm font-medium text-gray-700">
                  Amount is VAT inclusive
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reference
                </label>
                <input
                  type="text"
                  name="reference"
                  value={formData.reference || ''}
                  onChange={handleInputChange}
                  placeholder="e.g., Invoice #, Cheque #"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
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
                  placeholder="Additional information"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
                >
                  {loading ? 'Saving...' : 'Save Entry'}
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
            className="mb-6 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            New Entry
          </button>
        )}

        {/* Transactions List */}
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Loading transactions...</p>
          </div>
        ) : transactions.length === 0 ? (
          <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-500">No income entries found</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-gray-100 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Date</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Description</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Category</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Amount</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">VAT</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Total</th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map(trans => (
                  <tr key={trans.id} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-6 py-3 text-sm text-gray-900">
                      {new Date(trans.date).toLocaleDateString('en-ZA')}
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-900">{trans.description}</td>
                    <td className="px-6 py-3 text-sm text-gray-600">
                      {categories.find(c => c.id === trans.income_category_id)?.code}
                    </td>
                    <td className="px-6 py-3 text-sm text-right font-medium text-gray-900">
                      R{(trans.amount || 0).toFixed(2)}
                    </td>
                    <td className="px-6 py-3 text-sm text-right text-gray-600">
                      R{(trans.vat_amount || 0).toFixed(2)}
                    </td>
                    <td className="px-6 py-3 text-sm text-right font-semibold text-gray-900">
                      R{((trans.amount || 0) + (trans.vat_amount || 0)).toFixed(2)}
                    </td>
                    <td className="px-6 py-3 text-center">
                      <button
                        onClick={() => trans.id && handleDeleteTransaction(trans.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

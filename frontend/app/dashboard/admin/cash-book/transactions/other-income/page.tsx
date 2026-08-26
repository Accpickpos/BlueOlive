'use client';

import { useState, useEffect } from 'react';
import { Plus, AlertCircle, CheckCircle2 } from 'lucide-react';
import cashBookApi from '@/lib/cashBookApi';
import { getApiErrorMessage } from '@/lib/api';
import { IncomeCategory, OtherIncomeEntry } from '@/lib/types/cashBook';
import { BalanceCard } from '@/components/cash-book';

// Backend only supports these discrete tax codes — there is no free-form
// VAT-rate input (see CashBookVATService.TAX_CODE_MAP).
const TAX_CODES = [
  { value: 1, label: 'Standard Rated (14%)', rate: 0.14 },
  { value: 2, label: 'Zero-rated (0%)', rate: 0 },
  { value: 3, label: 'Exempt (0%)', rate: 0 },
  { value: 4, label: 'Foreign Transaction (0%)', rate: 0 },
];

const num = (v: string | number | undefined) => (typeof v === 'string' ? parseFloat(v) || 0 : v || 0);

export default function OtherIncomeEntryPage() {
  const [categories, setCategories] = useState<IncomeCategory[]>([]);
  const [transactions, setTransactions] = useState<OtherIncomeEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    transaction_date: new Date().toISOString().split('T')[0],
    description: '',
    value_excl_vat: 0,
    income_category_id: 0,
    tax_code: 1,
    reference: '',
    notes: '',
    paid_into: 'CASH' as 'CASH' | 'BANK',
    bank_account_number: '',
  });

  const [totals, setTotals] = useState({
    totalExclVat: 0,
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
      const entries = (transactionsRes.results || []) as unknown as OtherIncomeEntry[];
      setTransactions(entries);
      calculateTotals(entries);
    } catch (err) {
      setError('Failed to load data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const calculateTotals = (entries: OtherIncomeEntry[]) => {
    const totals = entries.reduce(
      (acc, e) => ({
        totalExclVat: acc.totalExclVat + num(e.transaction?.value_excl_vat),
        totalVAT: acc.totalVAT + num(e.transaction?.tax_amount),
        totalInclusive: acc.totalInclusive + num(e.transaction?.total_incl_vat),
      }),
      { totalExclVat: 0, totalVAT: 0, totalInclusive: 0 }
    );
    setTotals(totals);
  };

  const vatPreview = (() => {
    const rate = TAX_CODES.find((t) => t.value === formData.tax_code)?.rate || 0;
    const vat = formData.value_excl_vat * rate;
    return { vat, total: formData.value_excl_vat + vat };
  })();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!formData.income_category_id || !formData.value_excl_vat || !formData.description || !formData.transaction_date) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);

    try {
      // description is the only free-text field the backend stores per
      // transaction — fold "notes" into it rather than silently dropping it.
      const description = formData.notes
        ? `${formData.description} — ${formData.notes}`
        : formData.description;

      await cashBookApi.otherIncome.create({
        transaction_date: formData.transaction_date,
        description,
        value_excl_vat: formData.value_excl_vat,
        income_category_id: formData.income_category_id,
        tax_code: formData.tax_code,
        reference: formData.reference,
        paid_into: formData.paid_into,
        bank_account_number: formData.paid_into === 'BANK' ? formData.bank_account_number : '',
      });

      setSuccess('Other income entry created successfully!');

      setFormData({
        transaction_date: new Date().toISOString().split('T')[0],
        description: '',
        value_excl_vat: 0,
        income_category_id: 0,
        tax_code: 1,
        reference: '',
        notes: '',
        paid_into: 'CASH',
        bank_account_number: '',
      });
      setShowForm(false);

      await fetchData();
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to create entry'));
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
          <BalanceCard title="Total Income (Excl. VAT)" amount={totals.totalExclVat} variant="income" />
          <BalanceCard title="Total VAT" amount={totals.totalVAT} variant="default" />
          <BalanceCard title="Gross Amount" amount={totals.totalInclusive} variant="balance" />
        </div>

        {/* Entry Form */}
        {showForm && (
          <div className="mb-6 bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
            <h2 className="text-xl font-bold mb-4">New Income Entry</h2>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Date *</label>
                  <input
                    type="date"
                    name="transaction_date"
                    value={formData.transaction_date}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Income Category *</label>
                  <select
                    name="income_category_id"
                    value={formData.income_category_id}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  >
                    <option value={0}>Select Category</option>
                    {categories.filter((c) => c.is_active).map((cat) => (
                      <option key={cat.id} value={cat.id || 0}>
                        {cat.code} - {cat.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
                <input
                  type="text"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="e.g., Commission received from partner"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Amount (Excl. VAT) *</label>
                  <input
                    type="number"
                    name="value_excl_vat"
                    value={formData.value_excl_vat}
                    onChange={handleInputChange}
                    placeholder="0.00"
                    step="0.01"
                    min="0"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tax Code</label>
                  <select
                    name="tax_code"
                    value={formData.tax_code}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  >
                    {TAX_CODES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">VAT Amount (calculated)</label>
                  <input
                    type="text"
                    value={vatPreview.vat.toFixed(2)}
                    disabled
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Paid Into</label>
                  <select
                    name="paid_into"
                    value={formData.paid_into}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  >
                    <option value="CASH">Cash Till</option>
                    <option value="BANK">Bank Account</option>
                  </select>
                </div>
                {formData.paid_into === 'BANK' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Bank Account Number</label>
                    <input
                      type="text"
                      name="bank_account_number"
                      value={formData.bank_account_number}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                )}
              </div>

              <p className="text-sm text-gray-500">
                Total (incl. VAT): <span className="font-semibold text-gray-900">R{vatPreview.total.toFixed(2)}</span>
              </p>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reference</label>
                <input
                  type="text"
                  name="reference"
                  value={formData.reference}
                  onChange={handleInputChange}
                  placeholder="e.g., Invoice #, Cheque #"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleInputChange}
                  placeholder="Additional information (appended to the description)"
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
                </tr>
              </thead>
              <tbody>
                {transactions.map((entry) => (
                  <tr key={entry.id} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-6 py-3 text-sm text-gray-900">
                      {entry.transaction?.transaction_date
                        ? new Date(entry.transaction.transaction_date).toLocaleDateString('en-ZA')
                        : '-'}
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-900">{entry.transaction?.description}</td>
                    <td className="px-6 py-3 text-sm text-gray-600">{entry.category_name}</td>
                    <td className="px-6 py-3 text-sm text-right font-medium text-gray-900">
                      R{num(entry.transaction?.value_excl_vat).toFixed(2)}
                    </td>
                    <td className="px-6 py-3 text-sm text-right text-gray-600">
                      R{num(entry.transaction?.tax_amount).toFixed(2)}
                    </td>
                    <td className="px-6 py-3 text-sm text-right font-semibold text-gray-900">
                      R{num(entry.transaction?.total_incl_vat).toFixed(2)}
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

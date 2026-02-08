'use client';

import { useState, useEffect } from 'react';
import { ChevronLeft, Download, Eye } from 'lucide-react';
import creditorsApi from '@/lib/creditorsApi';

interface Transaction {
  id: number;
  supplier: string;
  transaction_type: string;
  transaction_number: string;
  invoice_number: string;
  transaction_date: string;
  amount_inclusive: number;
  vat_amount: number;
  balance_due: number;
  is_allocated: boolean;
}

interface TransactionsListProps {
  onBack: () => void;
}

const transactionTypeLabels: { [key: string]: string } = {
  INVOICE_STOCK: 'Stock Receiving',
  RETURN_STOCK: 'Stock Return',
  INVOICE_EXPENSE: 'Expense Invoice',
  RETURN_EXPENSE: 'Expense Return',
  PAYMENT: 'Payment',
  JOURNAL: 'Journal Entry',
  RFC: 'Return for Credit',
};

export default function TransactionsList({ onBack }: TransactionsListProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [filteredTransactions, setFilteredTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    transactionType: '',
    startDate: '',
    endDate: '',
    searchTerm: '',
  });

  useEffect(() => {
    fetchTransactions();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [transactions, filters]);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const response = await creditorsApi.transactions.list();
      setTransactions(Array.isArray(response) ? response : []);
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...transactions];

    if (filters.transactionType) {
      filtered = filtered.filter((t) => t.transaction_type === filters.transactionType);
    }

    if (filters.startDate) {
      filtered = filtered.filter((t) => new Date(t.transaction_date) >= new Date(filters.startDate));
    }

    if (filters.endDate) {
      filtered = filtered.filter((t) => new Date(t.transaction_date) <= new Date(filters.endDate));
    }

    if (filters.searchTerm) {
      const term = filters.searchTerm.toLowerCase();
      filtered = filtered.filter((t) =>
        t.supplier.toLowerCase().includes(term) ||
        t.transaction_number.toLowerCase().includes(term) ||
        t.invoice_number.toLowerCase().includes(term)
      );
    }

    setFilteredTransactions(filtered);
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters({ ...filters, [name]: value });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-ZA');
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">Creditors - Transactions List</h2>
          <p className="text-gray-600 mt-1">Total: {filteredTransactions.length} transactions</p>
        </div>
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:text-blue-800 font-medium"
        >
          <ChevronLeft className="w-5 h-5" />
          Back to Menu
        </button>
      </div>

      {/* Filters */}
      <div className="bg-gray-50 p-4 rounded-lg mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Transaction Type
          </label>
          <select
            name="transactionType"
            value={filters.transactionType}
            onChange={handleFilterChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Types</option>
            {Object.entries(transactionTypeLabels).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            type="date"
            name="startDate"
            value={filters.startDate}
            onChange={handleFilterChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Date
          </label>
          <input
            type="date"
            name="endDate"
            value={filters.endDate}
            onChange={handleFilterChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search
          </label>
          <input
            type="text"
            name="searchTerm"
            value={filters.searchTerm}
            onChange={handleFilterChange}
            placeholder="Supplier, Ref, Invoice #"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center py-8">
          <p className="text-gray-600">Loading transactions...</p>
        </div>
      ) : filteredTransactions.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-600">No transactions found</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b-2 border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-900">Date</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900">Type</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900">Supplier</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900">Ref #</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-900">Invoice #</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-900">Amount</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-900">VAT</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-900">Balance Due</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-900">Status</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-900">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.map((txn) => (
                <tr key={txn.id} className="border-b hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-gray-700">{formatDate(txn.transaction_date)}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                      {transactionTypeLabels[txn.transaction_type] || txn.transaction_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700">{txn.supplier}</td>
                  <td className="px-4 py-3 font-mono text-gray-700">{txn.transaction_number}</td>
                  <td className="px-4 py-3 font-mono text-gray-700">{txn.invoice_number || '-'}</td>
                  <td className="px-4 py-3 text-right text-gray-900 font-semibold">
                    {formatCurrency(txn.amount_inclusive)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(txn.vat_amount)}</td>
                  <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(txn.balance_due)}</td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        txn.is_allocated
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {txn.is_allocated ? 'Allocated' : 'Pending'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button className="text-blue-600 hover:text-blue-800 p-1">
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Summary */}
      {filteredTransactions.length > 0 && (
        <div className="mt-6 border-t pt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <p className="text-sm text-gray-600 mb-1">Total Transactions</p>
            <p className="text-2xl font-bold text-blue-900">{filteredTransactions.length}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <p className="text-sm text-gray-600 mb-1">Total Amount</p>
            <p className="text-2xl font-bold text-green-900">
              {formatCurrency(
                filteredTransactions.reduce((sum, t) => sum + t.amount_inclusive, 0)
              )}
            </p>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
            <p className="text-sm text-gray-600 mb-1">Total VAT</p>
            <p className="text-2xl font-bold text-orange-900">
              {formatCurrency(filteredTransactions.reduce((sum, t) => sum + t.vat_amount, 0))}
            </p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <p className="text-sm text-gray-600 mb-1">Outstanding Balance</p>
            <p className="text-2xl font-bold text-purple-900">
              {formatCurrency(filteredTransactions.reduce((sum, t) => sum + t.balance_due, 0))}
            </p>
          </div>
        </div>
      )}

      {/* Export Button */}
      <div className="mt-6 flex gap-3">
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
          <Download className="w-4 h-4" />
          Export to CSV
        </button>
      </div>
    </div>
  );
}

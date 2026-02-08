'use client';

import React, { useState, useEffect } from 'react';
import { 
  Supplier, 
  OutstandingBalance, 
  useCreditorsAPI 
} from '@/lib/creditorsApi';
import OutstandingBalanceForm from './OutstandingBalanceForm';

export default function OutstandingBalanceMaintenance() {
  const api = useCreditorsAPI();
  const [balances, setBalances] = useState<OutstandingBalance[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedBalance, setSelectedBalance] = useState<OutstandingBalance | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [filterSupplier, setFilterSupplier] = useState<number | null>(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [totalOutstanding, setTotalOutstanding] = useState<string | number>('0.00');

  useEffect(() => {
    loadSuppliers();
    loadBalances();
  }, []);

  const loadSuppliers = async () => {
    try {
      const data = await api.listSuppliers({});
      setSuppliers(data.results || []);
    } catch (err: any) {
      console.error('Failed to load suppliers:', err);
    }
  };

  const loadBalances = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading outstanding balances...');
      const data = await api.listOutstandingBalances({
        supplier_account_number: filterSupplier || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      });
      console.log('Outstanding balances response:', data);
      setBalances(data.items || []);
      setTotalOutstanding(data.total_outstanding || '0.00');
      
      // If no data, check if endpoint is available
      if (data.items.length === 0 && data.count === 0) {
        console.warn('No outstanding balance data returned - endpoint may not be fully implemented');
      }
    } catch (err: any) {
      console.error('Failed to load balances:', err);
      // Check if it's a database/table issue
      if (err.message?.includes('500') || err.message?.includes('table')) {
        setError('Outstanding Balance feature is not yet available. The backend endpoint is still being implemented.');
      } else if (err.response?.status === 404) {
        setError('Outstanding Balance feature is not yet available. The backend endpoint is still being implemented.');
      } else {
        setError('Failed to load outstanding balances');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number | undefined) => {
    if (!id) return;
    if (!confirm('Are you sure you want to delete this outstanding balance record?')) return;

    try {
      await api.deleteOutstandingBalance(id);
      setBalances(balances.filter(b => b.id !== id));
      alert('Outstanding balance record deleted successfully');
    } catch (err: any) {
      console.error('Failed to delete record:', err);
      alert(`Failed to delete: ${err.message}`);
    }
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setSelectedBalance(null);
    loadBalances();
  };

  const handleEdit = (balance: OutstandingBalance) => {
    setSelectedBalance(balance);
    setShowForm(true);
  };

  const handleCreateNew = () => {
    setSelectedBalance(null);
    setShowForm(true);
  };

  const handleApplyFilters = () => {
    loadBalances();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Outstanding Balance Capture</h2>
        <button
          onClick={handleCreateNew}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          + Capture Balance
        </button>
      </div>

      {/* Summary Section */}
      <div className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-4">
        <div className="text-sm font-semibold text-blue-600 uppercase tracking-wide mb-1">Total Outstanding</div>
        <div className="text-3xl font-bold text-blue-900">
          R{typeof totalOutstanding === 'number' ? totalOutstanding.toFixed(2) : parseFloat(totalOutstanding as string).toFixed(2)}
        </div>
        <div className="text-sm text-blue-700 mt-2">Across {balances.length} transaction(s)</div>
      </div>

      {/* Form Section */}
      {showForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">
            {selectedBalance ? 'Edit Outstanding Balance' : 'Capture Outstanding Balance'}
          </h3>
          <OutstandingBalanceForm
            suppliers={suppliers}
            balance={selectedBalance || undefined}
            onSuccess={handleFormSuccess}
            onCancel={() => {
              setShowForm(false);
              setSelectedBalance(null);
            }}
          />
        </div>
      )}

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow p-4 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Supplier
            </label>
            <select
              value={filterSupplier || ''}
              onChange={(e) => setFilterSupplier(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Suppliers</option>
              {suppliers.map(supplier => (
                <option key={supplier.account_number} value={supplier.account_number}>
                  {supplier.account_number} - {supplier.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              To Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleApplyFilters}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Apply Filters
            </button>
          </div>
        </div>
      </div>

      {/* Balances List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {error && (
          <div className="bg-red-50 border-b border-red-200 text-red-700 px-4 py-3">
            {error}
          </div>
        )}

        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading outstanding balances...</div>
        ) : balances.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No outstanding balance records found
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Supplier</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Transaction #</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Transaction Date</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Original Amount</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Balance Due</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">Age Period</th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {balances.map((balance) => (
                <tr key={balance.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {balance.creditor_name}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {balance.transaction_number}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {new Date(balance.transaction_date).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    R{typeof balance.original_amount === 'number' ? balance.original_amount.toFixed(2) : parseFloat(balance.original_amount as string).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900">
                    R{typeof balance.balance_due === 'number' ? balance.balance_due.toFixed(2) : parseFloat(balance.balance_due as string).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {balance.age_period === 0 ? 'Current' : `${balance.age_period} days`}
                  </td>
                  <td className="px-4 py-3 text-sm text-center">
                    <div className="flex gap-2 justify-center">
                      <button
                        onClick={() => handleEdit(balance)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(balance.id)}
                        className="text-red-600 hover:text-red-800 font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

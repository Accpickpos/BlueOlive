'use client';

import { useState, useEffect } from 'react';
import { debtorsApi } from '@/lib/debtorsApi';
import type { DebtorAccount } from '@/lib/types/debtors';
import { Edit2, Trash2, Plus } from 'lucide-react';
import DebtorAccountForm from '@/components/debtors/forms/DebtorAccountForm';

interface DebtorsListProps {
  onRefresh?: number;
}

export default function DebtorsList({ onRefresh }: DebtorsListProps) {
  const [debtors, setDebtors] = useState<DebtorAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDebtor, setSelectedDebtor] = useState<DebtorAccount | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Load debtors
  const loadDebtors = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading debtors...');
      const params = searchQuery ? { search: searchQuery } : undefined;
      const data = await debtorsApi.accounts.list(params);
      console.log('Debtors API response:', data);
      
      // Handle both direct array and paginated response
      const debtorsList = Array.isArray(data) ? data : (data?.results || []);
      setDebtors(debtorsList);
    } catch (err: any) {
      console.error('Error loading debtors:', err);
      
      // Provide more helpful error messages
      let errorMessage = 'Failed to load debtors';
      if (err?.response?.status === 404) {
        errorMessage = 'Debtors endpoint not found. Please check the backend API configuration.';
      } else if (err?.response?.status === 500) {
        errorMessage = 'Server error while loading debtors. Please check the backend logs.';
      } else if (err?.message?.includes('Network')) {
        errorMessage = 'Network error. Is the backend running at ' + (process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000') + '?';
      }
      
      setError(errorMessage);
      setDebtors([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDebtors();
  }, []);

  // Refresh when onRefresh prop changes
  useEffect(() => {
    if (onRefresh !== undefined) {
      loadDebtors();
    }
  }, [onRefresh]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setSelectedDebtor(null);
    loadDebtors();
  };

  const handleEdit = (debtor: DebtorAccount) => {
    setSelectedDebtor(debtor);
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this debtor?')) return;

    try {
      await debtorsApi.accounts.delete(id);
      loadDebtors();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete debtor');
    }
  };

  const handleNewDebtor = () => {
    setSelectedDebtor(null);
    setShowForm(true);
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-semibold">Error</p>
          <p className="text-red-700 text-sm mt-1">{error}</p>
          <button
            onClick={() => setError(null)}
            className="mt-3 text-sm text-red-600 hover:text-red-800 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Form Section */}
      {showForm ? (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">
              {selectedDebtor ? `Edit Debtor: ${selectedDebtor.dname}` : 'New Debtor'}
            </h2>
            <button
              onClick={() => {
                setShowForm(false);
                setSelectedDebtor(null);
              }}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>
          <DebtorAccountForm
            initialData={selectedDebtor || undefined}
            isEdit={selectedDebtor !== null}
            onSuccess={handleFormSuccess}
          />
        </div>
      ) : (
        <>
          {/* Search and Controls */}
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <div className="flex gap-4 flex-wrap items-end">
              <div className="flex-1 min-w-[250px]">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search Debtors
                </label>
                <input
                  type="text"
                  placeholder="Search by name or account number..."
                  value={searchQuery}
                  onChange={handleSearch}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <button
                onClick={handleNewDebtor}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
              >
                <Plus size={20} />
                New Debtor
              </button>

              <button
                onClick={loadDebtors}
                disabled={loading}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                {loading ? 'Loading...' : 'Refresh'}
              </button>
            </div>
          </div>

          {/* Debtors List */}
          <div className="bg-white rounded-lg shadow overflow-x-auto">
            {loading ? (
              <div className="p-8 text-center text-gray-500">Loading debtors...</div>
            ) : debtors.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No debtors found. {searchQuery && 'Try a different search.'}
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Account #
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Contact
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Balance
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {debtors.map((debtor) => (
                    <tr key={debtor.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {debtor.dno}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {debtor.dname}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {debtor.email || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {typeof debtor.total_balance === 'number'
                          ? debtor.total_balance.toFixed(2)
                          : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            debtor.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {debtor.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                        <button
                          onClick={() => handleEdit(debtor)}
                          className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-900"
                        >
                          <Edit2 size={16} />
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(debtor.id)}
                          className="inline-flex items-center gap-1 text-red-600 hover:text-red-900"
                        >
                          <Trash2 size={16} />
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}

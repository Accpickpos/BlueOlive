'use client';

import { useState, useEffect } from 'react';
import { Supplier, useCreditorsAPI } from '@/lib/creditorsApi';
import CreditorForm from './CreditorForm';
import { Edit2, Trash2, Plus } from 'lucide-react';

export default function CreditorsMaintenance() {
  const api = useCreditorsAPI();

  const [creditors, setCreditors] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCreditor, setSelectedCreditor] = useState<Supplier | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | null>(null);

  // Load creditors
  const loadCreditors = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading creditors with filters:', { searchQuery, filterActive });
      const data = await api.listSuppliers({
        search: searchQuery || undefined,
        is_active: filterActive !== null ? filterActive : undefined,
      });
      console.log('Creditors list response:', data);
      console.log('data.results:', data.results);
      setCreditors(data.results || []);
    } catch (err) {
      console.error('Error loading creditors:', err);
      setError(err instanceof Error ? err.message : 'Failed to load creditors');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCreditors();
  }, []);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleFilterChange = (value: string) => {
    if (value === 'all') {
      setFilterActive(null);
    } else if (value === 'active') {
      setFilterActive(true);
    } else {
      setFilterActive(false);
    }
  };

  const handleFormSuccess = (creditor: Supplier) => {
    setShowForm(false);
    setSelectedCreditor(null);
    loadCreditors();
  };

  const handleEdit = (creditor: Supplier) => {
    setSelectedCreditor(creditor);
    setShowForm(true);
  };

  const handleDelete = async (accountNumber: number) => {
    if (!confirm('Are you sure you want to delete this creditor?')) return;

    try {
      await api.deleteSupplier(accountNumber);
      loadCreditors();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete creditor');
    }
  };

  const handleNewCreditor = () => {
    setSelectedCreditor(null);
    setShowForm(true);
  };

  const handleApplyFilters = () => {
    loadCreditors();
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <button
            onClick={() => setError(null)}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
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
              {selectedCreditor ? `Edit Creditor: ${selectedCreditor.name}` : 'New Creditor'}
            </h2>
            <button
              onClick={() => {
                setShowForm(false);
                setSelectedCreditor(null);
              }}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>
          <CreditorForm
            creditor={selectedCreditor || undefined}
            onSuccess={handleFormSuccess}
            onCancel={() => {
              setShowForm(false);
              setSelectedCreditor(null);
            }}
          />
        </div>
      ) : (
        <>
          {/* Search and Filters */}
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <div className="flex gap-4 flex-wrap">
              <div className="flex-1 min-w-[250px]">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search Creditors
                </label>
                <input
                  type="text"
                  placeholder="Search by name or account number..."
                  value={searchQuery}
                  onChange={handleSearch}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="w-40">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <select
                  value={filterActive === null ? 'all' : filterActive ? 'active' : 'inactive'}
                  onChange={(e) => handleFilterChange(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              <div className="flex gap-2 items-end">
                <button
                  onClick={handleApplyFilters}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                >
                  Apply Filters
                </button>
                <button
                  onClick={handleNewCreditor}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium flex items-center gap-2"
                >
                  <Plus size={20} />
                  New Creditor
                </button>
              </div>
            </div>
          </div>

          {/* Creditors Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {loading ? (
              <div className="p-6 text-center text-gray-500">
                Loading creditors...
              </div>
            ) : creditors.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                <p>No creditors found.</p>
                <button
                  onClick={handleNewCreditor}
                  className="mt-4 text-blue-600 hover:text-blue-800 underline font-medium"
                >
                  Create the first creditor
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Account #
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Short Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Email
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Phone
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Balance
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {creditors.map((creditor) => (
                      <tr key={creditor.account_number} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {creditor.account_number}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {creditor.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {creditor.short_name || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {creditor.email || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {creditor.telephone1 || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                          {typeof creditor.total_balance === 'number'
                            ? `R${creditor.total_balance.toFixed(2)}`
                            : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span
                            className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              creditor.is_active
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {creditor.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                          <button
                            onClick={() => handleEdit(creditor)}
                            className="text-blue-600 hover:text-blue-900 inline-flex items-center gap-1"
                          >
                            <Edit2 size={16} />
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(creditor.account_number)}
                            className="text-red-600 hover:text-red-900 inline-flex items-center gap-1"
                          >
                            <Trash2 size={16} />
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

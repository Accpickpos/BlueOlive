'use client';

import { useState, useEffect, useCallback } from 'react';
import { Supplier, useCreditorsAPI } from '@/lib/creditorsApi';
import CreditorForm from './CreditorForm';
import CreditorsFilters from './CreditorsFilters';
import CreditorsTable from './CreditorsTable';
import CreditorsPagination from './CreditorsPagination';

export default function CreditorsMaintenance() {
  const api = useCreditorsAPI();

  const [creditors, setCreditors] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCreditor, setSelectedCreditor] = useState<Supplier | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pageSize] = useState(20);

  // Load creditors
  const loadCreditors = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading creditors with filters:', { searchQuery, filterActive, page });
      const data = await api.listSuppliers({
        search: searchQuery || undefined,
        is_active: filterActive !== null ? filterActive : undefined,
        page,
        page_size: pageSize,
      });
      console.log('Creditors list response:', data);
      // Handle paginated response - data.results contains the array
      const creditorsArray = data?.results || data;
      setCreditors(Array.isArray(creditorsArray) ? creditorsArray : []);
      setTotal(data?.count || 0);
    } catch (err) {
      console.error('Error loading creditors:', err);
      setError(err instanceof Error ? err.message : 'Failed to load creditors');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, filterActive, page, pageSize, api]);

  useEffect(() => {
    loadCreditors();
  }, [loadCreditors]);

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
    setPage(1); // Reset to first page when filters change - useEffect will auto-trigger loadCreditors
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
          {/* CreditorsFilters */}
          <CreditorsFilters
            searchQuery={searchQuery}
            filterActive={filterActive}
            onSearchChange={handleSearch}
            onFilterChange={handleFilterChange}
            onApplyFilters={handleApplyFilters}
            onNewCreditor={handleNewCreditor}
          />

          {/* CreditorsTable */}
          <CreditorsTable
            creditors={creditors}
            loading={loading}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onNewCreditor={handleNewCreditor}
          />

          {/* CreditorsPagination */}
          <CreditorsPagination
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}

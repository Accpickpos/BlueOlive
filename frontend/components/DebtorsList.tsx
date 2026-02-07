'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiRequest } from '@/lib/api';

interface Debtor {
  id: number;
  account_number: string;
  name: string;
  contact_person: string;
  email: string;
  telephone1: string;
  sales_area_name: string | null;
  account_category: string;
  credit_limit: number;
  current_balance: number;
  is_active: boolean;
  is_blocked: boolean;
}

interface DebtorsListProps {
  onSelectDebtor?: (debtorId: number) => void;
  onRefresh?: number;
}

export default function DebtorsList({ onSelectDebtor, onRefresh }: DebtorsListProps) {
  const [debtors, setDebtors] = useState<Debtor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchDebtors();
  }, [searchTerm, currentPage, onRefresh]);

  const fetchDebtors = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
      });

      if (searchTerm) {
        params.append('search', searchTerm);
      }

      const response = await apiRequest(`/api/debtors/?${params}`);

      // Handle both paginated and direct array responses
      if (response.data.results && Array.isArray(response.data.results)) {
        setDebtors(response.data.results);
        setTotalCount(response.data.count || 0);
      } else if (Array.isArray(response.data)) {
        setDebtors(response.data);
        setTotalCount(response.data.length);
      } else {
        setDebtors([]);
        setTotalCount(0);
      }
      setError(null);
    } catch (err) {
      setError('Failed to load debtors');
      console.error(err);
      setDebtors([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (debtorId: number) => {
    if (!window.confirm('Are you sure you want to delete this debtor?')) {
      return;
    }

    try {
      setDeleting(true);
      await apiRequest(`/api/debtors/${debtorId}/`, {
        method: 'DELETE',
      });
      setDeleteId(null);
      fetchDebtors();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete debtor');
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  const getCategoryLabel = (category: string) => {
    const labels: { [key: string]: string } = {
      '': 'Balance Forward',
      'O': 'Open Item',
      'C': 'Cash Customer',
    };
    return labels[category] || category;
  };

  if (loading) {
    return <div className="text-center py-8">Loading debtors...</div>;
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Search Bar */}
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search by account number, name, or contact..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1);
          }}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
        />
        <Link
          href="/dashboard/admin/debtors/maintenance/create"
          className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          Add Debtor
        </Link>
      </div>

      {/* Table */}
      <div className="overflow-x-auto bg-white rounded-lg shadow">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 border-b">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Account #</th>
              <th className="px-4 py-3 text-left font-semibold">Name</th>
              <th className="px-4 py-3 text-left font-semibold">Contact</th>
              <th className="px-4 py-3 text-left font-semibold">Email</th>
              <th className="px-4 py-3 text-left font-semibold">Category</th>
              <th className="px-4 py-3 text-right font-semibold">Credit Limit</th>
              <th className="px-4 py-3 text-right font-semibold">Balance</th>
              <th className="px-4 py-3 text-left font-semibold">Status</th>
              <th className="px-4 py-3 text-center font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {debtors.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                  No debtors found
                </td>
              </tr>
            ) : (
              debtors.map((debtor) => (
                <tr key={debtor.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono font-semibold">{debtor.account_number}</td>
                  <td className="px-4 py-3">{debtor.name}</td>
                  <td className="px-4 py-3">{debtor.contact_person || '-'}</td>
                  <td className="px-4 py-3 text-sm">{debtor.email || '-'}</td>
                  <td className="px-4 py-3 text-sm">
                    {getCategoryLabel(debtor.account_category)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    R {parseFloat(String(debtor.credit_limit)).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold">
                    <span
                      className={parseFloat(String(debtor.current_balance)) > 0 ? 'text-red-600' : 'text-green-600'}
                    >
                      R {parseFloat(String(debtor.current_balance)).toFixed(2)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {debtor.is_blocked && (
                        <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
                          Blocked
                        </span>
                      )}
                      {!debtor.is_active && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                          Inactive
                        </span>
                      )}
                      {!debtor.is_blocked && debtor.is_active && (
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                          Active
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2 justify-center">
                      <Link
                        href={`/dashboard/admin/debtors/maintenance/${debtor.id}/balance`}
                        className="text-green-600 hover:text-green-800 font-medium text-sm"
                        title="View Account Balance"
                      >
                        Balance
                      </Link>
                      <Link
                        href={`/dashboard/admin/debtors/maintenance/${debtor.id}`}
                        className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                      >
                        Edit
                      </Link>
                      <button
                        onClick={() => handleDelete(debtor.id)}
                        disabled={deleting}
                        className="text-red-600 hover:text-red-800 font-medium text-sm disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Showing {(currentPage - 1) * pageSize + 1} to{' '}
            {Math.min(currentPage * pageSize, totalCount)} of {totalCount} debtors
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50"
            >
              Previous
            </button>
            <div className="flex items-center gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`px-3 py-1 border rounded ${
                    currentPage === page
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  {page}
                </button>
              ))}
            </div>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

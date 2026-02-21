'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import Link from 'next/link';
import { debtorsApi } from '@/lib/debtorsApi';
import type { DebtorAccount } from '@/lib/types/debtors';
import { Edit2, Trash2, Plus, Search, AlertCircle, Eye, X } from 'lucide-react';
import DebtorAccountForm from '@/components/debtors/forms/DebtorAccountForm';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

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
  const [filters, setFilters] = useState({
    blocked: false as boolean | undefined,
    is_active: true,
  });
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  // Debounced search with delay
  const [debouncedSearch, setDebouncedSearch] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Load debtors
  const loadDebtors = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await debtorsApi.accounts.list({
        search: debouncedSearch || undefined,
        is_active: filters.is_active,
        blocked: filters.blocked,
        page,
        page_size: 20,
      });
      
      // Handle both direct array and paginated response
      if (Array.isArray(data)) {
        setDebtors(data);
        setTotal(data.length);
      } else {
        setDebtors(data?.results || []);
        setTotal(data?.count || 0);
      }
    } catch (err: any) {
      console.error('Error loading debtors:', err);
      
      let errorMessage = 'Failed to load debtors';
      if (err?.response?.status === 404) {
        errorMessage = 'Debtors endpoint not found. Please check the backend API configuration.';
      } else if (err?.response?.status === 500) {
        errorMessage = 'Server error while loading debtors. Please check the backend logs.';
      } else if (err?.message?.includes('Network')) {
        errorMessage = 'Network error. Is the backend running?';
      }
      
      setError(errorMessage);
      setDebtors([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, filters, page]);

  useEffect(() => {
    loadDebtors();
  }, [loadDebtors]);

  // Refresh when onRefresh prop changes
  useEffect(() => {
    if (onRefresh !== undefined) {
      loadDebtors();
    }
  }, [onRefresh, loadDebtors]);

  const handleFormSuccess = () => {
    setShowForm(false);
    setSelectedDebtor(null);
    loadDebtors();
  };

  const handleEdit = (debtor: DebtorAccount) => {
    setSelectedDebtor(debtor);
    setShowForm(true);
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Delete ${name}?`)) return;

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

  const totalPages = Math.ceil(total / 20);
  const hasActiveFilters = Boolean(debouncedSearch || filters.blocked);

  return (
    <div className="space-y-6">
      {/* Form Modal */}
      {showForm ? (
        <Card className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">
              {selectedDebtor ? `Edit Debtor: ${selectedDebtor.dname}` : 'New Debtor'}
            </h2>
            <button
              onClick={() => {
                setShowForm(false);
                setSelectedDebtor(null);
              }}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <DebtorAccountForm
            initialData={selectedDebtor || undefined}
            isEdit={selectedDebtor !== null}
            onSuccess={handleFormSuccess}
          />
        </Card>
      ) : (
        <>
          {/* Header */}
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold">Debtors</h1>
              <p className="text-gray-600 mt-1">Manage customer accounts and credit settings</p>
            </div>
            <Button 
              onClick={handleNewDebtor}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Debtor
            </Button>
          </div>

          {/* Search & Filters */}
          <Card className="p-4">
            <div className="space-y-4">
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <Input
                    placeholder="Search by name, number, or email..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="flex-1 pl-10"
                  />
                </div>
              </div>

              <div className="flex gap-2 flex-wrap">
                <Button
                  variant={!filters.blocked ? 'default' : 'outline'}
                  onClick={() => {
                    setFilters({ ...filters, blocked: false });
                    setPage(1);
                  }}
                >
                  Active
                </Button>
                <Button
                  variant={filters.blocked ? 'default' : 'outline'}
                  onClick={() => {
                    setFilters({ ...filters, blocked: true });
                    setPage(1);
                  }}
                >
                  Blocked
                </Button>
                {hasActiveFilters && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSearchQuery('');
                      setFilters({ blocked: false, is_active: true });
                      setPage(1);
                    }}
                  >
                    Clear Filters
                  </Button>
                )}
              </div>
            </div>
          </Card>

          {/* Error State */}
          {error && (
            <Card className="p-4 bg-red-50 border border-red-200">
              <div className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-red-800 font-semibold">Error</p>
                  <p className="text-red-700 text-sm mt-1">{error}</p>
                  <button
                    onClick={() => setError(null)}
                    className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </Card>
          )}

          {/* Table */}
          <Card className="p-4 overflow-x-auto">
            {loading ? (
              <div className="py-8 text-center text-gray-600">Loading debtors...</div>
            ) : debtors.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-gray-600">No debtors found</p>
                {debouncedSearch && <p className="text-sm text-gray-500 mt-1">Try a different search</p>}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">Account #</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">Name</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">Contact</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">Sales Area</th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">Balance</th>
                      <th className="px-4 py-3 text-right font-semibold text-gray-700">Credit Limit</th>
                      <th className="px-4 py-3 text-center font-semibold text-gray-700">Status</th>
                      <th className="px-4 py-3 text-center font-semibold text-gray-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {debtors.map((debtor) => (
                      <tr key={debtor.id} className="border-b hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 font-medium">{debtor.dno}</td>
                        <td className="px-4 py-3">{debtor.dname}</td>
                        <td className="px-4 py-3 text-gray-600">{debtor.dcontact || '-'}</td>
                        <td className="px-4 py-3 text-gray-600">{debtor.darea_name || '-'}</td>
                        <td className="px-4 py-3 text-right font-semibold text-blue-600">
                          ${debtor.total_balance?.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-3 text-right">${debtor.dclimit?.toLocaleString()}</td>
                        <td className="px-4 py-3 text-center">
                          {debtor.blockflag ? (
                            <Badge className="bg-red-500">Blocked</Badge>
                          ) : debtor.is_active ? (
                            <Badge className="bg-green-500">Active</Badge>
                          ) : (
                            <Badge className="bg-gray-500">Inactive</Badge>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex justify-center gap-2">
                            <Link href={`/dashboard/admin/debtors/maintenance/${debtor.id}`}>
                              <Button variant="outline" size="sm" title="View details">
                                <Eye className="w-4 h-4" />
                              </Button>
                            </Link>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEdit(debtor)}
                              title="Edit debtor"
                            >
                              <Edit2 className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDelete(debtor.id, debtor.dname)}
                              title="Delete debtor"
                            >
                              <Trash2 className="w-4 h-4 text-red-600" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <Button
                  key={p}
                  variant={page === p ? 'default' : 'outline'}
                  onClick={() => setPage(p)}
                >
                  {p}
                </Button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

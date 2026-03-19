'use client';

import React, {
  useState,
  useMemo,
  useCallback,
  useEffect,
  memo,
} from 'react';
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

const currencyFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 2,
});

const PAGE_SIZE = 20;

/* =========================
   Memoized Row Component
========================= */

interface DebtorRowProps {
  debtor: DebtorAccount;
  onEdit: (debtor: DebtorAccount) => void;
  onDelete: (id: number, name: string) => void;
}

const DebtorRow = memo(function DebtorRow({
  debtor,
  onEdit,
  onDelete,
}: DebtorRowProps) {
  const handleEdit = useCallback(() => {
    onEdit(debtor);
  }, [onEdit, debtor]);

  const handleDelete = useCallback(() => {
    onDelete(debtor.id, debtor.name);
  }, [onDelete, debtor.id, debtor.name]);

  return (
    <tr className="border-b hover:bg-gray-50 transition-colors">
      <td className="px-4 py-3 font-medium">{debtor.customer_number}</td>
      <td className="px-4 py-3">{debtor.name}</td>
      <td className="px-4 py-3 text-gray-600">
        {debtor.contact_person || '-'}
      </td>
      <td className="px-4 py-3 text-gray-600">
        {debtor.area_code ?? '-'}
      </td>
      <td className="px-4 py-3 text-right font-semibold text-blue-600">
        ${currencyFormatter.format(debtor.total_balance ?? 0)}
      </td>
      <td className="px-4 py-3 text-right">
        ${currencyFormatter.format(debtor.credit_limit ?? 0)}
      </td>
      <td className="px-4 py-3 text-center">
        {debtor.is_blocked_flag ? (
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
            <Button variant="outline" size="sm">
              <Eye className="w-4 h-4" />
            </Button>
          </Link>
          <Button variant="outline" size="sm" onClick={handleEdit}>
            <Edit2 className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={handleDelete}>
            <Trash2 className="w-4 h-4 text-red-600" />
          </Button>
        </div>
      </td>
    </tr>
  );
});

/* =========================
   Main Component
========================= */

function DebtorsListComponent({ onRefresh }: DebtorsListProps) {
  const [debtors, setDebtors] = useState<DebtorAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDebtor, setSelectedDebtor] = useState<DebtorAccount | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] =
    useState<'all' | 'active' | 'blocked'>('all');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [debouncedSearch, setDebouncedSearch] = useState('');

  /* =========================
     Debounce Search
  ========================= */

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  /* =========================
     Load Debtors
  ========================= */

  const loadDebtors = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const apiFilters: Record<string, any> = {
        search: debouncedSearch || undefined,
        page,
        page_size: PAGE_SIZE,
      };

      if (filterType === 'active') {
        apiFilters.is_active = true;
        apiFilters.blockflag__in = ['0', 'N'];
      } else if (filterType === 'blocked') {
        apiFilters.blockflag__in = ['1', '2', '3', 'Y'];
      }

      const data = await debtorsApi.accounts.list(apiFilters);

      if (Array.isArray(data)) {
        setDebtors(data);
        setTotal(data.length);
      } else {
        setDebtors(data?.results ?? []);
        setTotal(data?.count ?? 0);
      }
    } catch (err: any) {
      setError(err?.message ?? 'Failed to load debtors');
      setDebtors([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, filterType, page]);

  useEffect(() => {
    loadDebtors();
  }, [loadDebtors]);

  useEffect(() => {
    if (onRefresh !== undefined) {
      loadDebtors();
    }
  }, [onRefresh, loadDebtors]);

  /* =========================
     Stable Handlers
  ========================= */

  const handleEdit = useCallback((debtor: DebtorAccount) => {
    setSelectedDebtor(debtor);
    setShowForm(true);
  }, []);

  const handleDelete = useCallback(
    async (id: number, name: string) => {
      if (!confirm(`Delete ${name}?`)) return;
      await debtorsApi.accounts.delete(id);
      loadDebtors();
    },
    [loadDebtors]
  );

  const handleNewDebtor = useCallback(() => {
    setSelectedDebtor(null);
    setShowForm(true);
  }, []);

  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setFilterType('all');
    setPage(1);
  }, []);

  /* =========================
     Derived Values
  ========================= */

  const totalPages = useMemo(
    () => Math.ceil(total / PAGE_SIZE),
    [total]
  );

  const paginationPages = useMemo(
    () => Array.from({ length: totalPages }, (_, i) => i + 1),
    [totalPages]
  );

  const hasActiveFilters = useMemo(
    () => Boolean(debouncedSearch || filterType !== 'all'),
    [debouncedSearch, filterType]
  );

  /* =========================
     Render
  ========================= */

  return (
    <div className="space-y-6">
      {showForm ? (
        <Card className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">
              {selectedDebtor
                ? `Edit Debtor: ${selectedDebtor.name}`
                : 'New Debtor'}
            </h2>
            <button onClick={() => setShowForm(false)}>
              <X className="w-5 h-5" />
            </button>
          </div>
          <DebtorAccountForm
            initialData={selectedDebtor ?? undefined}
            isEdit={!!selectedDebtor}
            onSuccess={() => {
              setShowForm(false);
              setSelectedDebtor(null);
              loadDebtors();
            }}
          />
        </Card>
      ) : (
        <>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold">Debtors</h1>
              <p className="text-gray-600 mt-1">
                Manage customer accounts and credit settings
              </p>
            </div>
            <Button onClick={handleNewDebtor}>
              <Plus className="w-4 h-4 mr-2" />
              New Debtor
            </Button>
          </div>

          <Card className="p-4 space-y-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="flex gap-2 flex-wrap">
              {(['all', 'active', 'blocked'] as const).map((type) => (
                <Button
                  key={type}
                  variant={filterType === type ? 'default' : 'outline'}
                  onClick={() => {
                    setFilterType(type);
                    setPage(1);
                  }}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </Button>
              ))}

              {hasActiveFilters && (
                <Button variant="outline" onClick={clearFilters}>
                  Clear Filters
                </Button>
              )}
            </div>
          </Card>

          <Card className="p-4 overflow-x-auto">
            {loading ? (
              <div className="py-8 text-center">Loading debtors...</div>
            ) : (
              <table className="w-full text-sm">
                <tbody>
                  {debtors.map((debtor) => (
                    <DebtorRow
                      key={debtor.id}
                      debtor={debtor}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                    />
                  ))}
                </tbody>
              </table>
            )}
          </Card>

          {totalPages > 1 && (
            <div className="flex justify-center gap-2">
              {paginationPages.map((p) => (
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

export default memo(DebtorsListComponent);
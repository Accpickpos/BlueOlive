'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { PlusCircle, Search, AlertCircle } from 'lucide-react';

const TYPE_LABELS: Record<string, string> = {
  CASH_SALE: 'Cash Sale',
  INVOICE: 'Invoice',
  RECEIPT: 'Receipt on Account',
  CREDIT_NOTE: 'Credit Note',
  LAYBYE: 'Laybye',
  QUOTATION: 'Quotation',
  JOB_CARD: 'Job Card',
  REPAIR: 'Repair',
  PAYOUT: 'Payout',
};

const STATUS_CLASSES: Record<string, string> = {
  OPEN: 'bg-blue-100 text-blue-800',
  IN_PROGRESS: 'bg-yellow-100 text-yellow-800',
  RESOLVED: 'bg-green-100 text-green-800',
  CLOSED: 'bg-gray-100 text-gray-800',
};

export default function TransactionQueryPage() {
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const posAPIRef = useRef(posAPI);

  const [queries, setQueries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  useEffect(() => {
    if (authLoading || !user) return;
    let cancelled = false;

    const fetchQueries = async () => {
      setLoading(true);
      try {
        const response = await posAPIRef.current.listTransactionQueries({
          query_status: statusFilter === 'all' ? undefined : (statusFilter as any),
          page: currentPage,
        });
        if (cancelled) return;

        const raw: any[] = Array.isArray(response) ? response : (response as any).results ?? [];
        setQueries(
          raw.map((q: any) => ({
            id: q.id,
            query_number: q.query_number ?? '',
            query_date: q.query_date ?? '',
            transaction_type: q.transaction_type_display ?? TYPE_LABELS[q.transaction_type] ?? q.transaction_type,
            transaction_number: q.transaction_number ?? '',
            customer_name: q.customer_name ?? '',
            query_description: q.query_description ?? '',
            query_status: q.query_status ?? 'OPEN',
            assigned_to_name: q.assigned_to_name ?? '',
          }))
        );
      } catch (error) {
        if (!cancelled) {
          console.error('Error fetching transaction queries:', error);
          setQueries([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchQueries();
    return () => { cancelled = true; };
  }, [user, authLoading, statusFilter, currentPage]);

  const filteredQueries = queries.filter((q) =>
    !searchTerm ||
    q.query_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    q.transaction_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    q.customer_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleResolve = async (id: number) => {
    const notes = window.prompt('Resolution notes:');
    if (notes === null) return;
    setResolvingId(id);
    try {
      await posAPIRef.current.resolveTransactionQuery(id, notes);
      setQueries((prev) => prev.map((q) => (q.id === id ? { ...q, query_status: 'RESOLVED' } : q)));
    } catch (error) {
      console.error('Error resolving query:', error);
    } finally {
      setResolvingId(null);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Transaction Query</h1>
            <p className="text-sm text-gray-500">Log and resolve customer queries about past transactions</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard/pos/transaction-query/create"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              New Query
            </Link>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white border-b px-6 py-4">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="flex-1 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by query number, transaction number or customer..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 border rounded-lg bg-white font-medium"
          >
            <option value="all">All Status</option>
            <option value="OPEN">Open</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>
          <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
            Search
          </Button>
        </form>
      </div>

      {/* Queries Table */}
      <div className="p-6">
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">Loading queries...</p>
          </div>
        ) : filteredQueries.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-4">No transaction queries found</p>
                <Link href="/dashboard/pos/transaction-query/create">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <PlusCircle className="w-4 h-4 mr-2" />
                    Log First Query
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Query #</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Transaction #</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Assigned To</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredQueries.map((q) => (
                    <TableRow key={q.id}>
                      <TableCell className="font-medium">{q.query_number}</TableCell>
                      <TableCell>{q.transaction_type}</TableCell>
                      <TableCell>{q.transaction_number}</TableCell>
                      <TableCell>{q.customer_name || '-'}</TableCell>
                      <TableCell className="max-w-xs truncate">{q.query_description}</TableCell>
                      <TableCell>{q.assigned_to_name || '-'}</TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-sm font-medium ${STATUS_CLASSES[q.query_status] || 'bg-gray-100 text-gray-800'}`}>
                          {q.query_status.replace('_', ' ')}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        {q.query_status !== 'RESOLVED' && q.query_status !== 'CLOSED' && (
                          <button
                            onClick={() => handleResolve(q.id)}
                            disabled={resolvingId === q.id}
                            className="text-blue-600 hover:text-blue-700 text-sm font-medium disabled:opacity-50"
                          >
                            {resolvingId === q.id ? 'Resolving...' : 'Resolve'}
                          </button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Pagination */}
      {filteredQueries.length > 0 && (
        <div className="flex justify-between items-center px-6 py-4 bg-white border-t">
          <p className="text-sm text-gray-600">Page {currentPage}</p>
          <div className="flex gap-2">
            <Button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              variant="outline"
            >
              Previous
            </Button>
            <Button
              onClick={() => setCurrentPage(currentPage + 1)}
              variant="outline"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

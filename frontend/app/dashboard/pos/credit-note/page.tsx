'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import {
  PlusCircle,
  Search,
  AlertCircle,
} from 'lucide-react';

export default function CreditNotesPage() {
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const posAPIRef = useRef(posAPI);
  const [creditNotes, setCreditNotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (authLoading || !user) return;
    let cancelled = false;

    const fetchCreditNotes = async () => {
      setLoading(true);
      try {
        const response = await posAPIRef.current.listCreditNotes({
          is_posted: statusFilter === 'all' ? undefined : statusFilter === 'posted',
          page: currentPage,
        });
        if (cancelled) return;

        const raw: any[] = Array.isArray(response) ? response : (response as any).results ?? [];
        setCreditNotes(
          raw.map((cn: any) => ({
            id: cn.id,
            reference: cn.credit_number ?? String(cn.id),
            customer: cn.customer_name || 'Unknown',
            debtor_account: cn.debtor_account ?? '',
            original_sale_number: cn.original_sale_number ?? '',
            amount: Number(cn.total_amount ?? 0),
            refund_type: cn.refund_type_display ?? cn.refund_type ?? 'CASH',
            date: cn.credit_date ?? '',
            is_posted: !!cn.is_posted,
          }))
        );
      } catch (error) {
        if (!cancelled) {
          console.error('Error fetching credit notes:', error);
          setCreditNotes([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchCreditNotes();
    return () => { cancelled = true; };
  }, [user, authLoading, statusFilter, currentPage]);

  const filteredCreditNotes = creditNotes.filter((cn) =>
    !searchTerm ||
    cn.reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cn.customer.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
            <h1 className="text-2xl font-bold text-gray-900">Credit Notes</h1>
            <p className="text-sm text-gray-500">Create returns from original invoice or standalone credit notes</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard/pos/credit-note/create"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              New Credit Note
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
                placeholder="Search by reference or customer..."
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
            <option value="posted">Posted</option>
            <option value="pending">Pending</option>
          </select>
          <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
            Search
          </Button>
        </form>
      </div>

      {/* Credit Notes Table */}
      <div className="p-6">
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">Loading credit notes...</p>
          </div>
        ) : filteredCreditNotes.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-4">No credit notes found</p>
                <Link href="/dashboard/pos/credit-note/create">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <PlusCircle className="w-4 h-4 mr-2" />
                    Create First Credit Note
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
                    <TableHead>Reference</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Original Sale</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Refund Type</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCreditNotes.map((cn) => (
                    <TableRow key={cn.id}>
                      <TableCell className="font-medium">{cn.reference}</TableCell>
                      <TableCell>{cn.customer}</TableCell>
                      <TableCell>{cn.date ? new Date(cn.date).toLocaleDateString() : '—'}</TableCell>
                      <TableCell>{cn.original_sale_number || '-'}</TableCell>
                      <TableCell className="text-right font-medium">
                        R{cn.amount.toFixed(2)}
                      </TableCell>
                      <TableCell>{cn.refund_type}</TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-sm font-medium ${
                          cn.is_posted ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {cn.is_posted ? 'Posted' : 'Pending'}
                        </span>
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
      {filteredCreditNotes.length > 0 && (
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

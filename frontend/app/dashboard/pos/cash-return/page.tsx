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
  Eye,
  Printer,
  Download,
  AlertCircle,
} from 'lucide-react';

export default function CashReturnPage() {
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const posAPIRef = useRef(posAPI);
  const [returns, setReturns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (authLoading || !user) return;
    let cancelled = false;

    const fetchReturns = async () => {
      setLoading(true);
      try {
        const response = await posAPIRef.current.listCashReturns({
          is_posted: statusFilter === 'completed' ? true : statusFilter === 'pending' ? false : undefined,
          page: currentPage,
        });
        if (cancelled) return;

        const raw: any[] = Array.isArray(response) ? response : (response as any).results ?? [];
        setReturns(
          raw.map((ret: any) => ({
            id: ret.id,
            reference: ret.return_number ?? String(ret.id),
            original_sale: ret.original_sale_number ?? '',
            customer: ret.customer_name || 'Walk-in Customer',
            amount: Number(ret.total_amount ?? 0),
            date: ret.return_date ?? '',
            status: ret.is_posted ? 'completed' : 'pending',
          }))
        );
      } catch (error) {
        if (!cancelled) {
          console.error('Error fetching returns:', error);
          setReturns([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchReturns();
    return () => { cancelled = true; };
  }, [user, authLoading, statusFilter, currentPage]);

  const filteredReturns = returns.filter((ret) =>
    !searchTerm ||
    ret.reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ret.original_sale.toLowerCase().includes(searchTerm.toLowerCase())
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
            <h1 className="text-2xl font-bold text-gray-900">Cash Returns</h1>
            <p className="text-sm text-gray-500">Process refunds for cash sales with tender return</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard/pos/cash-return/create"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              New Cash Return
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
                placeholder="Search by reference or original sale..."
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
            <option value="completed">Posted</option>
            <option value="pending">Pending</option>
          </select>
          <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
            Search
          </Button>
        </form>
      </div>

      {/* Cash Returns Table */}
      <div className="p-6">
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">Loading cash returns...</p>
          </div>
        ) : filteredReturns.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-4">No cash returns found</p>
                <Link href="/dashboard/pos/cash-return/create">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <PlusCircle className="w-4 h-4 mr-2" />
                    Create First Cash Return
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
                    <TableHead>Original Sale</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Refund Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredReturns.map((ret) => (
                    <TableRow key={ret.id}>
                      <TableCell className="font-medium">{ret.reference}</TableCell>
                      <TableCell>{ret.original_sale}</TableCell>
                      <TableCell>{ret.date ? new Date(ret.date).toLocaleDateString() : '—'}</TableCell>
                      <TableCell className="text-right font-medium">
                        R{ret.amount?.toFixed(2) || '0.00'}
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-sm font-medium ${
                          ret.status === 'completed' ? 'bg-green-100 text-green-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {ret.status?.charAt(0).toUpperCase() + ret.status?.slice(1)}
                        </span>
                      </TableCell>
                      <TableCell className="text-right space-x-2">
                        <button className="text-blue-600 hover:text-blue-700">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="text-green-600 hover:text-green-700">
                          <Printer className="w-4 h-4" />
                        </button>
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
      {filteredReturns.length > 0 && (
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

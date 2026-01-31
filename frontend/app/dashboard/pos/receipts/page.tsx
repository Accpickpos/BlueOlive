'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
  AlertCircle,
  Plus,
  ArrowLeft,
  Search,
  Filter,
  Download,
  Eye,
  FileText,
} from 'lucide-react';
import { ErrorAlert, SuccessAlert, LoadingOverlay } from '@/components/pos/form-components';

export default function ReceiptsList() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const posAPI = usePOSAPI(user?.tenant?.slug);

  const [receipts, setReceipts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Fetch receipts
  useEffect(() => {
    const fetchReceipts = async () => {
      try {
        setLoading(true);
        setError(null);

        const params: any = {};
        if (dateFrom) params.from_date = dateFrom;
        if (dateTo) params.to_date = dateTo;
        if (filterStatus !== 'all') params.status = filterStatus;

        const response = await posAPI.listReceipts(params);
        const data = response?.results || response || [];
        setReceipts(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Error fetching receipts:', err);
        setError(err instanceof Error ? err.message : 'Failed to load receipts');
        setReceipts([]);
      } finally {
        setLoading(false);
      }
    };

    if (user?.tenant?.slug) {
      fetchReceipts();
    }
  }, [user?.tenant?.slug]);

  // Filter receipts
  const filteredReceipts = receipts.filter((receipt) => {
    const matchesSearch =
      receipt.debtor_account_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      receipt.receipt_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      receipt.notes?.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesSearch;
  });

  const handleDelete = async (id: string) => {
    // Delete functionality not yet implemented in API
    setError('Delete functionality is not yet available');
    setTimeout(() => setError(null), 3000);
  };

  const handleExport = () => {
    // CSV export functionality
    const csv = [
      ['Receipt #', 'Account', 'Amount', 'Type', 'Date', 'Status'],
      ...filteredReceipts.map((r) => [
        r.receipt_number,
        r.debtor_account_number,
        r.amount,
        r.receipt_type,
        new Date(r.receipt_date).toLocaleDateString(),
        r.status,
      ]),
    ]
      .map((row) => row.join(','))
      .join('\n');

    const element = document.createElement('a');
    element.setAttribute('href', `data:text/csv;charset=utf-8,${encodeURIComponent(csv)}`);
    element.setAttribute('download', `receipts-${new Date().toISOString().split('T')[0]}.csv`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  if (authLoading) {
    return <LoadingOverlay message="Loading..." />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 p-6 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push('/dashboard/pos')}
              className="hover:bg-slate-200"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Payment Receipts</h1>
              <p className="text-slate-600 mt-1">Manage customer payment records</p>
            </div>
          </div>
          <Link href="/dashboard/pos/receipts/create">
            <Button className="gap-2 bg-blue-600 hover:bg-blue-700">
              <Plus className="h-4 w-4" />
              New Receipt
            </Button>
          </Link>
        </div>

        {/* Alerts */}
        {error && <ErrorAlert message={error} />}
        {success && <SuccessAlert message={success} />}

        {/* Filters & Search */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Filters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Search */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="Receipt # or Account..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Date From */}
              <div className="space-y-2">
                <label className="text-sm font-medium">From Date</label>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>

              {/* Date To */}
              <div className="space-y-2">
                <label className="text-sm font-medium">To Date</label>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>

              {/* Status Filter */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Status</label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="DRAFT">Draft</option>
                  <option value="POSTED">Posted</option>
                  <option value="CANCELLED">Cancelled</option>
                </select>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setSearchTerm('');
                  setFilterStatus('all');
                  setDateFrom('');
                  setDateTo('');
                }}
              >
                Clear Filters
              </Button>
              {filteredReceipts.length > 0 && (
                <Button
                  variant="outline"
                  onClick={handleExport}
                  className="gap-2"
                >
                  <Download className="h-4 w-4" />
                  Export CSV
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Results Summary */}
        <div className="text-sm text-slate-600">
          Showing <span className="font-semibold text-slate-900">{filteredReceipts.length}</span> of{' '}
          <span className="font-semibold text-slate-900">{receipts.length}</span> receipts
        </div>

        {/* Receipts Table */}
        {loading ? (
          <LoadingOverlay message="Loading receipts..." />
        ) : filteredReceipts.length === 0 ? (
          <Card>
            <CardContent className="pt-12 pb-12 text-center">
              <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600 font-medium mb-2">No receipts found</p>
              <p className="text-slate-500 text-sm mb-4">
                {receipts.length === 0
                  ? 'Create your first receipt to get started'
                  : 'Try adjusting your filters'}
              </p>
              {receipts.length === 0 && (
                <Link href="/dashboard/pos/receipts/create">
                  <Button className="gap-2">
                    <Plus className="h-4 w-4" />
                    Create Receipt
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50 hover:bg-slate-50">
                      <TableHead>Receipt #</TableHead>
                      <TableHead>Account</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredReceipts.map((receipt) => (
                      <TableRow key={receipt.id} className="hover:bg-slate-50">
                        <TableCell className="font-medium text-slate-900">
                          {receipt.receipt_number || 'N/A'}
                        </TableCell>
                        <TableCell>{receipt.debtor_account_number}</TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {receipt.receipt_type?.replace(/_/g, ' ')}
                          </span>
                        </TableCell>
                        <TableCell className="text-right font-semibold">
                          R{receipt.amount?.toFixed(2) || '0.00'}
                        </TableCell>
                        <TableCell>
                          {new Date(receipt.receipt_date).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <span
                            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                              receipt.status === 'POSTED'
                                ? 'bg-green-100 text-green-700'
                                : receipt.status === 'DRAFT'
                                  ? 'bg-yellow-100 text-yellow-700'
                                  : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {receipt.status}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Link href={`/dashboard/pos/receipts/${receipt.id}`}>
                              <Button size="sm" variant="ghost">
                                <Eye className="h-4 w-4" />
                              </Button>
                            </Link>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDelete(receipt.id)}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              Delete
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

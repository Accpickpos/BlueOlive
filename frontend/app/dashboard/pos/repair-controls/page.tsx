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

const STATUS_LABELS: Record<string, string> = {
  C: 'Created',
  I: 'Issued to Supplier',
  R: 'Received from Supplier',
  V: 'Invoiced',
  X: 'Cancelled',
};

const STATUS_CLASSES: Record<string, string> = {
  C: 'bg-gray-100 text-gray-800',
  I: 'bg-yellow-100 text-yellow-800',
  R: 'bg-purple-100 text-purple-800',
  V: 'bg-green-100 text-green-800',
  X: 'bg-red-100 text-red-800',
};

export default function RepairControlPage() {
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const posAPIRef = useRef(posAPI);
  const [repairs, setRepairs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (authLoading || !user) return;
    let cancelled = false;

    const fetchRepairs = async () => {
      setLoading(true);
      try {
        const response = await posAPIRef.current.listRepairControls({
          status: statusFilter === 'all' ? undefined : (statusFilter as 'C' | 'I' | 'R' | 'V' | 'X'),
          page: currentPage,
        });
        if (cancelled) return;

        const raw: any[] = Array.isArray(response) ? response : (response as any).results ?? [];
        setRepairs(
          raw.map((r: any) => ({
            id: r.id,
            reference: r.repair_number ?? String(r.id),
            customer_name: r.customer_name ?? '',
            repair_details: r.repair_details ?? '',
            date_required: r.date_required ?? '',
            quoted_value: r.quoted_value != null ? Number(r.quoted_value) : null,
            telephone: r.telephone ?? '',
            status: r.status ?? 'C',
          }))
        );
      } catch (error) {
        if (!cancelled) {
          console.error('Error fetching repairs:', error);
          setRepairs([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchRepairs();
    return () => { cancelled = true; };
  }, [user, authLoading, statusFilter, currentPage]);

  const filteredRepairs = repairs.filter((r) =>
    !searchTerm ||
    r.reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.customer_name.toLowerCase().includes(searchTerm.toLowerCase())
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
            <h1 className="text-2xl font-bold text-gray-900">Repair Controls</h1>
            <p className="text-sm text-gray-500">Repair voucher management, supplier tracking, billing</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard/pos/repair-controls/create"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              New Repair
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
                placeholder="Search by reference or item..."
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
            <option value="C">Created</option>
            <option value="I">Issued to Supplier</option>
            <option value="R">Received from Supplier</option>
            <option value="V">Invoiced</option>
            <option value="X">Cancelled</option>
          </select>
          <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
            Search
          </Button>
        </form>
      </div>

      {/* Repairs Table */}
      <div className="p-6">
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">Loading repairs...</p>
          </div>
        ) : filteredRepairs.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-4">No repair jobs found</p>
                <Link href="/dashboard/pos/repair-controls/create">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <PlusCircle className="w-4 h-4 mr-2" />
                    Create First Repair
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
                    <TableHead>Repair Details</TableHead>
                    <TableHead>Date Required</TableHead>
                    <TableHead className="text-right">Quoted Value</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRepairs.map((repair) => (
                    <TableRow key={repair.id}>
                      <TableCell className="font-medium">{repair.reference}</TableCell>
                      <TableCell>{repair.customer_name}</TableCell>
                      <TableCell className="max-w-xs truncate">{repair.repair_details}</TableCell>
                      <TableCell>{repair.date_required ? new Date(repair.date_required).toLocaleDateString() : '—'}</TableCell>
                      <TableCell className="text-right font-medium">
                        {repair.quoted_value != null ? `R${repair.quoted_value.toFixed(2)}` : '—'}
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-sm font-medium ${STATUS_CLASSES[repair.status] || 'bg-gray-100 text-gray-800'}`}>
                          {STATUS_LABELS[repair.status] || repair.status}
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
      {filteredRepairs.length > 0 && (
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

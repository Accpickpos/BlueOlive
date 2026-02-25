'use client';

import { useState, useEffect } from 'react';
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

export default function CashSalesPage() {
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [cashSales, setCashSales] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (!authLoading && user) {
      fetchCashSales();
    }
  }, [user, authLoading, statusFilter, currentPage]);

  const fetchCashSales = async () => {
    setLoading(true);
    try {
      // Actually call the API to fetch cash sales
      const response = await posAPI.listCashSales();
      
      // Transform API response to match frontend structure
      const salesData = response.results || [];
      setCashSales(salesData.map((sale: any) => ({
        id: sale.id,
        reference: sale.sale_number,
        customer: sale.customer_name || 'Walk-in Customer',
        items: sale.line_count || 0,
        // Ensure amount is a number (API returns Decimal as string)
        total: Number(sale.total_amount) || 0,
        amount: Number(sale.total_amount) || 0,
        payment_method: 'cash', // Will be determined from tenders
        date: sale.sale_date,
        status: sale.is_cancelled ? 'cancelled' : 'completed',
        change: Number(sale.change_given) || 0,
      })));
    } catch (error) {
      console.error('Error fetching cash sales:', error);
      setCashSales([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchCashSales();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Cash Sales</h1>
            <p className="text-sm text-gray-500">Immediate cash and card transactions with tender routine</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard/pos/cash-sales/create"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              New Cash Sale
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
                placeholder="Search by reference or receipt..."
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
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
            Search
          </Button>
        </form>
      </div>

      {/* Cash Sales Table */}
      <div className="p-6">
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">Loading cash sales...</p>
          </div>
        ) : cashSales.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-4">No cash sales found</p>
                <Link href="/dashboard/pos/cash-sales/create">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <PlusCircle className="w-4 h-4 mr-2" />
                    Create First Cash Sale
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
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Payment Method</TableHead>
                    <TableHead>Change</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cashSales.map((sale) => (
                    <TableRow key={sale.id}>
                      <TableCell className="font-medium">
                        <Link href={`/dashboard/pos/cash-sales/${sale.id}`} className="text-blue-600 hover:text-blue-700">
                          {sale.reference}
                        </Link>
                      </TableCell>
                      <TableCell>{new Date(sale.date).toLocaleDateString()}</TableCell>
                      <TableCell className="text-right font-medium">
                        R{sale.total?.toFixed(2) || '0.00'}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm capitalize">{sale.payment_method}</span>
                      </TableCell>
                      <TableCell>R{sale.change?.toFixed(2) || '0.00'}</TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-sm font-medium ${
                          sale.status === 'completed' ? 'bg-green-100 text-green-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {sale.status?.charAt(0).toUpperCase() + sale.status?.slice(1)}
                        </span>
                      </TableCell>
                      <TableCell className="text-right space-x-2">
                        <Link href={`/dashboard/pos/cash-sales/${sale.id}`} className="text-blue-600 hover:text-blue-700">
                          <Eye className="w-4 h-4" />
                        </Link>
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
      {cashSales.length > 0 && (
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

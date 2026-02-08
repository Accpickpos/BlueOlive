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

export default function ChequeCashingPage() {
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [cheques, setCheques] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    fetchCheques();
  }, [statusFilter, currentPage]);

  const fetchCheques = async () => {
    setLoading(true);
    try {
      // API call would go here
      // const response = await posAPI.cheques.list(params);
      // For now, show demo data
      setTimeout(() => {
        setCheques([
          { id: 1, cheque_number: 'CHQ-001', customer_name: 'ABC Trading', bank_name: 'First National Bank', date: new Date(Date.now() - 86400000).toISOString(), amount: 5000, status: 'cashed' },
          { id: 2, cheque_number: 'CHQ-002', customer_name: 'XYZ Corp', bank_name: 'Standard Bank', date: new Date(Date.now() - 172800000).toISOString(), amount: 3200, status: 'pending' },
        ]);
      }, 300);
    } catch (error) {
      console.error('Error fetching cheques:', error);
    } finally {
      setTimeout(() => setLoading(false), 400);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchCheques();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Cheque Cashing</h1>
            <p className="text-sm text-gray-500">Cheque cashing with bank details capture</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard/pos/cheque-cashing/create"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              New Cheque Cash
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
                placeholder="Search by cheque number or customer..."
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
            <option value="cashed">Cashed</option>
            <option value="pending">Pending</option>
            <option value="dishonoured">Dishonoured</option>
          </select>
          <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
            Search
          </Button>
        </form>
      </div>

      {/* Cheques Table */}
      <div className="p-6">
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">Loading cheques...</p>
          </div>
        ) : cheques.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-4">No cheques found</p>
                <Link href="/dashboard/pos/cheque-cashing/create">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <PlusCircle className="w-4 h-4 mr-2" />
                    Cash New Cheque
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
                    <TableHead>Cheque Number</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Bank</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cheques.map((cheque) => (
                    <TableRow key={cheque.id}>
                      <TableCell className="font-medium">{cheque.cheque_number}</TableCell>
                      <TableCell>{cheque.customer_name}</TableCell>
                      <TableCell>{cheque.bank_name}</TableCell>
                      <TableCell>{new Date(cheque.date).toLocaleDateString()}</TableCell>
                      <TableCell className="text-right font-medium">
                        R{cheque.amount?.toFixed(2) || '0.00'}
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-sm font-medium ${
                          cheque.status === 'cashed' ? 'bg-green-100 text-green-800' :
                          cheque.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {cheque.status?.charAt(0).toUpperCase() + cheque.status?.slice(1)}
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
      {cheques.length > 0 && (
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

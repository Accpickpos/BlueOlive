'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  FileText,
  Plus,
  Send,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Eye,
  Download,
  Search,
  Filter,
} from 'lucide-react';

interface InterBranchTransfer {
  id: number;
  transfer_number: string;
  from_branch: string;
  to_branch: string;
  status: 'pending' | 'in_transit' | 'received' | 'cancelled';
  items_count: number;
  total_value: number;
  created_at: string;
  expected_delivery_date: string;
}

export default function InterBranchTransferPage() {
  const { user, isLoading } = useAuth();
  const [transfers, setTransfers] = useState<InterBranchTransfer[]>([]);
  const [filteredTransfers, setFilteredTransfers] = useState<InterBranchTransfer[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTransfers = async () => {
      try {
        setLoading(true);
        setError(null);
        // TODO: Replace with actual API call
        // const response = await fetch(`/api/ibt/transfers?branch=${user?.branch_id}`);
        // const data = await response.json();
        // setTransfers(data);
        setTransfers([]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load inter-branch transfers');
      } finally {
        setLoading(false);
      }
    };

    if (user?.id) {
      fetchTransfers();
    }
  }, [user?.id]);

  // Filter transfers based on search and status
  useEffect(() => {
    let filtered = transfers;

    if (statusFilter !== 'all') {
      filtered = filtered.filter((t) => t.status === statusFilter);
    }

    if (searchTerm) {
      filtered = filtered.filter(
        (t) =>
          t.transfer_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
          t.from_branch.toLowerCase().includes(searchTerm.toLowerCase()) ||
          t.to_branch.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredTransfers(filtered);
  }, [transfers, searchTerm, statusFilter]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="h-12 w-12 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-600 font-medium">Loading inter-branch transfers...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-red-700">
              <AlertCircle className="h-5 w-5" />
              <p>Not authenticated</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'in_transit':
        return 'bg-blue-100 text-blue-800';
      case 'received':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <AlertCircle className="h-4 w-4" />;
      case 'in_transit':
        return <Send className="h-4 w-4" />;
      case 'received':
        return <CheckCircle className="h-4 w-4" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inter-Branch Transfers</h1>
          <p className="text-gray-600 mt-1">Manage stock transfers between branches</p>
        </div>
        <Link href="/dashboard/ibt/create">
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="h-4 w-4 mr-2" />
            New Transfer
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Transfers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">{transfers.length}</div>
            <p className="text-xs text-gray-500 mt-1">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">
              {transfers.filter((t) => t.status === 'pending').length}
            </div>
            <p className="text-xs text-gray-500 mt-1">Awaiting dispatch</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">In Transit</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {transfers.filter((t) => t.status === 'in_transit').length}
            </div>
            <p className="text-xs text-gray-500 mt-1">On the way</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Received</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {transfers.filter((t) => t.status === 'received').length}
            </div>
            <p className="text-xs text-gray-500 mt-1">Completed</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by transfer number, branch..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="in_transit">In Transit</option>
                <option value="received">Received</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Transfers Table */}
      <Card>
        <CardHeader>
          <CardTitle>Transfers</CardTitle>
          <CardDescription>{filteredTransfers.length} transfers found</CardDescription>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="text-center py-8">
              <div className="h-8 w-8 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-2" />
              <p className="text-slate-600">Loading...</p>
            </div>
          )}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          {!loading && filteredTransfers.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>No inter-branch transfers found</p>
              <Link href="/dashboard/ibt/create">
                <Button variant="outline" className="mt-4">
                  Create your first transfer
                </Button>
              </Link>
            </div>
          )}
          {!loading && filteredTransfers.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Transfer #</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">From</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">To</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Items</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Value</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Expected Delivery</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTransfers.map((transfer) => (
                    <tr key={transfer.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm font-medium text-gray-900">
                        {transfer.transfer_number}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">{transfer.from_branch}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{transfer.to_branch}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{transfer.items_count}</td>
                      <td className="py-3 px-4 text-sm font-medium text-gray-900">
                        R {transfer.total_value.toFixed(2)}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                            transfer.status
                          )}`}
                        >
                          {getStatusIcon(transfer.status)}
                          {transfer.status.replace('_', ' ').charAt(0).toUpperCase() +
                            transfer.status.slice(1).replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {new Date(transfer.expected_delivery_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <Link href={`/dashboard/ibt/${transfer.id}`}>
                            <Button size="sm" variant="outline">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

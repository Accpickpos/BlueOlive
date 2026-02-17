'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Package,
  Plus,
  CheckCircle,
  AlertCircle,
  Clock,
  Eye,
  Edit,
  Trash2,
  Search,
  Filter,
  BarChart,
} from 'lucide-react';

interface InterBranchItem {
  id: number;
  item_code: string;
  item_name: string;
  from_branch: string;
  to_branch: string;
  quantity: number;
  unit_cost: number;
  total_value: number;
  status: 'pending' | 'approved' | 'received' | 'rejected';
  requested_date: string;
  approval_date?: string;
  received_date?: string;
}

export default function InterBranchItemsPage() {
  const { user, isLoading } = useAuth();
  const [items, setItems] = useState<InterBranchItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<InterBranchItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchItems = async () => {
      try {
        setLoading(true);
        setError(null);
        // TODO: Replace with actual API call
        // const response = await fetch(`/api/ibi/items?branch=${user?.branch_id}`);
        // const data = await response.json();
        // setItems(data);
        setItems([]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load inter-branch items');
      } finally {
        setLoading(false);
      }
    };

    if (user?.id) {
      fetchItems();
    }
  }, [user?.id]);

  // Filter items based on search and status
  useEffect(() => {
    let filtered = items;

    if (statusFilter !== 'all') {
      filtered = filtered.filter((item) => item.status === statusFilter);
    }

    if (searchTerm) {
      filtered = filtered.filter(
        (item) =>
          item.item_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.item_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.from_branch.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.to_branch.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredItems(filtered);
  }, [items, searchTerm, statusFilter]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="h-12 w-12 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-600 font-medium">Loading inter-branch items...</p>
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
      case 'approved':
        return 'bg-blue-100 text-blue-800';
      case 'received':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4" />;
      case 'approved':
        return <CheckCircle className="h-4 w-4" />;
      case 'received':
        return <CheckCircle className="h-4 w-4" />;
      case 'rejected':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inter-Branch Items</h1>
          <p className="text-gray-600 mt-1">Manage individual item requests between branches</p>
        </div>
        <Link href="/dashboard/ibi/create">
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="h-4 w-4 mr-2" />
            New Request
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Items</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">{items.length}</div>
            <p className="text-xs text-gray-500 mt-1">All requests</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">
              {items.filter((i) => i.status === 'pending').length}
            </div>
            <p className="text-xs text-gray-500 mt-1">Awaiting approval</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Approved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {items.filter((i) => i.status === 'approved').length}
            </div>
            <p className="text-xs text-gray-500 mt-1">Ready to dispatch</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Received</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {items.filter((i) => i.status === 'received').length}
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
                  placeholder="Search by item code, name, branch..."
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
                <option value="approved">Approved</option>
                <option value="received">Received</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Items Table */}
      <Card>
        <CardHeader>
          <CardTitle>Items</CardTitle>
          <CardDescription>{filteredItems.length} items found</CardDescription>
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
          {!loading && filteredItems.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Package className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>No inter-branch items found</p>
              <Link href="/dashboard/ibi/create">
                <Button variant="outline" className="mt-4">
                  Create your first request
                </Button>
              </Link>
            </div>
          )}
          {!loading && filteredItems.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Item Code</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Item Name</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">From</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">To</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Qty</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Value</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Requested</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredItems.map((item) => (
                    <tr key={item.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm font-medium text-gray-900">
                        {item.item_code}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">{item.item_name}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{item.from_branch}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{item.to_branch}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{item.quantity}</td>
                      <td className="py-3 px-4 text-sm font-medium text-gray-900">
                        R {item.total_value.toFixed(2)}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                            item.status
                          )}`}
                        >
                          {getStatusIcon(item.status)}
                          {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {new Date(item.requested_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <Link href={`/dashboard/ibi/${item.id}`}>
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

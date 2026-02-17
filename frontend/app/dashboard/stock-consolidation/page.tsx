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
  TrendingDown,
  Eye,
  Download,
  Search,
  Filter,
  BarChart3,
  Layers,
} from 'lucide-react';

interface StockConsolidation {
  id: number;
  consolidation_number: string;
  consolidation_date: string;
  items_consolidated: number;
  total_units: number;
  total_value: number;
  status: 'in_progress' | 'completed' | 'cancelled';
  from_branches?: string;
  to_branch?: string;
  created_by: string;
  completed_date?: string;
}

export default function StockConsolidationPage() {
  const { user, isLoading } = useAuth();
  const [consolidations, setConsolidations] = useState<StockConsolidation[]>([]);
  const [filteredConsolidations, setFilteredConsolidations] = useState<StockConsolidation[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchConsolidations = async () => {
      try {
        setLoading(true);
        setError(null);
        // TODO: Replace with actual API call
        // const response = await fetch(`/api/stock-consolidation?branch=${user?.branch_id}`);
        // const data = await response.json();
        // setConsolidations(data);
        setConsolidations([]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load stock consolidations');
      } finally {
        setLoading(false);
      }
    };

    if (user?.id) {
      fetchConsolidations();
    }
  }, [user?.id]);

  // Filter consolidations based on search and status
  useEffect(() => {
    let filtered = consolidations;

    if (statusFilter !== 'all') {
      filtered = filtered.filter((c) => c.status === statusFilter);
    }

    if (searchTerm) {
      filtered = filtered.filter(
        (c) =>
          c.consolidation_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.created_by.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredConsolidations(filtered);
  }, [consolidations, searchTerm, statusFilter]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="h-12 w-12 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-600 font-medium">Loading stock consolidations...</p>
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
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'in_progress':
        return <Layers className="h-4 w-4" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4" />;
      case 'cancelled':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const totalConsolidatedValue = consolidations.reduce((sum, c) => sum + c.total_value, 0);
  const totalUnitsConsolidated = consolidations.reduce((sum, c) => sum + c.total_units, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Stock Consolidation</h1>
          <p className="text-gray-600 mt-1">Consolidate and manage stock across branches</p>
        </div>
        <Link href="/dashboard/stock-consolidation/create">
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="h-4 w-4 mr-2" />
            New Consolidation
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Consolidations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">{consolidations.length}</div>
            <p className="text-xs text-gray-500 mt-1">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">In Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {consolidations.filter((c) => c.status === 'in_progress').length}
            </div>
            <p className="text-xs text-gray-500 mt-1">Active consolidations</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {consolidations.filter((c) => c.status === 'completed').length}
            </div>
            <p className="text-xs text-gray-500 mt-1">Finalized</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">
              R {totalConsolidatedValue.toLocaleString('en-ZA', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
            <p className="text-xs text-gray-500 mt-1">Stock value</p>
          </CardContent>
        </Card>
      </div>

      {/* Additional Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Consolidation Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Units Consolidated</p>
              <p className="text-2xl font-bold text-gray-900">{totalUnitsConsolidated.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Average Units Per Consolidation</p>
              <p className="text-2xl font-bold text-gray-900">
                {consolidations.length > 0
                  ? (totalUnitsConsolidated / consolidations.length).toFixed(0)
                  : 0}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Average Value Per Consolidation</p>
              <p className="text-2xl font-bold text-gray-900">
                R{' '}
                {consolidations.length > 0
                  ? (totalConsolidatedValue / consolidations.length).toLocaleString('en-ZA', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })
                  : '0.00'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

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
                  placeholder="Search by consolidation number, user..."
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
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Consolidations Table */}
      <Card>
        <CardHeader>
          <CardTitle>Consolidations</CardTitle>
          <CardDescription>{filteredConsolidations.length} consolidations found</CardDescription>
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
          {!loading && filteredConsolidations.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Layers className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>No stock consolidations found</p>
              <Link href="/dashboard/stock-consolidation/create">
                <Button variant="outline" className="mt-4">
                  Create your first consolidation
                </Button>
              </Link>
            </div>
          )}
          {!loading && filteredConsolidations.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">
                      Consolidation #
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Date</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Items</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Units</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Value</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Created By</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredConsolidations.map((consolidation) => (
                    <tr key={consolidation.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm font-medium text-gray-900">
                        {consolidation.consolidation_number}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {new Date(consolidation.consolidation_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {consolidation.items_consolidated}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {consolidation.total_units.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-sm font-medium text-gray-900">
                        R {consolidation.total_value.toLocaleString('en-ZA', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                            consolidation.status
                          )}`}
                        >
                          {getStatusIcon(consolidation.status)}
                          {consolidation.status.replace('_', ' ').charAt(0).toUpperCase() +
                            consolidation.status.slice(1).replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {consolidation.created_by}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <Link href={`/dashboard/stock-consolidation/${consolidation.id}`}>
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

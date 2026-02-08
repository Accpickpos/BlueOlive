'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ArrowLeft, Search, AlertCircle, Download } from 'lucide-react';
import { apiRequest } from '@/lib/api';

interface SupplierDetails {
  account_number: number;
  name: string;
  account_type: string;
  email: string;
  telephone: string;
}

interface IndividualAccountData {
  supplier: SupplierDetails;
  balances: {
    current: number;
    '30_days': number;
    '60_days': number;
    '90_days': number;
    '120_days': number;
    '150_days': number;
    '180_days': number;
    total: number;
  };
  statistics: {
    amount_last_paid: number;
    date_last_paid: string | null;
    purchases_mtd: number;
    purchases_ytd: number;
  };
  recent_transactions: any[];
  open_items: any[];
}

export default function IndividualAccountEnquiry({ onBack }: { onBack: () => void }) {
  const [supplierId, setSupplierId] = useState('');
  const [showArchive, setShowArchive] = useState(false);
  const [data, setData] = useState<IndividualAccountData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'transactions' | 'openitems'>(
    'overview'
  );

  // Fetch suppliers for search
  useEffect(() => {
    const fetchSuppliers = async () => {
      try {
        const response = await apiRequest('/api/creditors/suppliers/');
        setSuppliers(response.data.results || response.data);
      } catch (err) {
        console.error('Error fetching suppliers:', err);
      }
    };

    fetchSuppliers();
  }, []);

  const handleSearch = async () => {
    if (!supplierId) {
      setError('Please enter a supplier account number');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await apiRequest(
        `/api/creditors/enquiries/individual_account/?supplier_id=${supplierId}&show_archive=${showArchive}`
      );

      if (response.status !== 200) {
        throw new Error('Supplier not found');
      }

      setData(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch supplier details');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
    }).format(value);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Individual Account Enquiry</h1>
          <p className="text-gray-600">View detailed creditor account information</p>
        </div>
      </div>

      {/* Search Section */}
      <Card>
        <CardHeader>
          <CardTitle>Search for Supplier</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium block mb-2">
                Supplier Account Number or Name
              </label>
              <Input
                placeholder="Enter account number or select from list"
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
                onKeyPress={handleKeyPress}
              />
            </div>

            {suppliers.length > 0 && (
              <div>
                <label className="text-sm font-medium block mb-2">Or Select from List</label>
                <Select value={supplierId} onValueChange={setSupplierId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select supplier..." />
                  </SelectTrigger>
                  <SelectContent>
                    {suppliers.map((supplier) => (
                      <SelectItem
                        key={supplier.account_number}
                        value={supplier.account_number.toString()}
                      >
                        {supplier.account_number} - {supplier.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="flex flex-col justify-end gap-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={showArchive}
                  onChange={(e) => setShowArchive(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Show Archive</span>
              </label>
              <Button onClick={handleSearch} disabled={loading}>
                <Search className="w-4 h-4 mr-2" />
                {loading ? 'Searching...' : 'Search'}
              </Button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-800">{error}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Section */}
      {data && (
        <>
          {/* Supplier Info */}
          <Card>
            <CardHeader>
              <CardTitle>Supplier Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-sm text-gray-600">Account Number</p>
                  <p className="text-lg font-semibold">{data.supplier.account_number}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Supplier Name</p>
                  <p className="text-lg font-semibold">{data.supplier.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Account Type</p>
                  <p className="text-lg font-semibold text-blue-600">{data.supplier.account_type}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Email</p>
                  <p className="text-sm break-all">{data.supplier.email || 'N/A'}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tab Navigation */}
          <div className="flex gap-4 border-b">
            {['overview', 'transactions', 'openitems'].map((tab) => (
              <button
                key={tab}
                onClick={() => setSelectedTab(tab as any)}
                className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
                  selectedTab === tab
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab === 'overview' && 'Overview'}
                {tab === 'transactions' && 'Recent Transactions'}
                {tab === 'openitems' && 'Open Items'}
              </button>
            ))}
          </div>

          {/* Overview Tab */}
          {selectedTab === 'overview' && (
            <>
              {/* Balance Summary */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                  <CardTitle>Balance Analysis</CardTitle>
                  <Button variant="outline" size="sm">
                    <Download className="w-4 h-4 mr-2" />
                    Print
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Current</p>
                      <p className="text-xl font-bold text-blue-600">
                        {formatCurrency(data.balances.current)}
                      </p>
                    </div>
                    <div className="bg-orange-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">30 Days</p>
                      <p className="text-xl font-bold text-orange-600">
                        {formatCurrency(data.balances['30_days'])}
                      </p>
                    </div>
                    <div className="bg-red-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">60 Days</p>
                      <p className="text-xl font-bold text-red-600">
                        {formatCurrency(data.balances['60_days'])}
                      </p>
                    </div>
                    <div className="bg-red-100 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">90+ Days</p>
                      <p className="text-xl font-bold text-red-700">
                        {formatCurrency(
                          data.balances['90_days'] +
                            data.balances['120_days'] +
                            data.balances['150_days'] +
                            data.balances['180_days']
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-gray-50 rounded-lg border-2 border-gray-200">
                    <p className="text-sm text-gray-600">Total Outstanding Balance</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {formatCurrency(data.balances.total)}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Statistics */}
              <Card>
                <CardHeader>
                  <CardTitle>Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-sm text-gray-600">Amount Last Paid</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(data.statistics.amount_last_paid)}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {data.statistics.date_last_paid
                          ? `on ${new Date(data.statistics.date_last_paid).toLocaleDateString()}`
                          : 'No payment recorded'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Purchases This Year</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(data.statistics.purchases_ytd)}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        MTD: {formatCurrency(data.statistics.purchases_mtd)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {/* Transactions Tab */}
          {selectedTab === 'transactions' && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                {data.recent_transactions.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-4 font-semibold">Date</th>
                          <th className="text-left py-2 px-4 font-semibold">Ref Number</th>
                          <th className="text-left py-2 px-4 font-semibold">Type</th>
                          <th className="text-right py-2 px-4 font-semibold">Net Amount</th>
                          <th className="text-right py-2 px-4 font-semibold">VAT</th>
                          <th className="text-right py-2 px-4 font-semibold">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.recent_transactions.map((txn: any, idx: number) => (
                          <tr key={idx} className="border-b hover:bg-gray-50">
                            <td className="py-2 px-4">
                              {new Date(txn.transaction_date).toLocaleDateString()}
                            </td>
                            <td className="py-2 px-4">{txn.transaction_number}</td>
                            <td className="py-2 px-4 text-xs">{txn.transaction_type}</td>
                            <td className="py-2 px-4 text-right">
                              {formatCurrency(txn.amount_exclusive)}
                            </td>
                            <td className="py-2 px-4 text-right">
                              {formatCurrency(txn.vat_amount)}
                            </td>
                            <td className="py-2 px-4 text-right font-semibold">
                              {formatCurrency(txn.amount_inclusive)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No transactions found</p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Open Items Tab */}
          {selectedTab === 'openitems' && (
            <Card>
              <CardHeader>
                <CardTitle>Open Items</CardTitle>
              </CardHeader>
              <CardContent>
                {data.open_items.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-4 font-semibold">Date</th>
                          <th className="text-left py-2 px-4 font-semibold">Ref Number</th>
                          <th className="text-left py-2 px-4 font-semibold">Type</th>
                          <th className="text-right py-2 px-4 font-semibold">Amount</th>
                          <th className="text-right py-2 px-4 font-semibold">Balance Due</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.open_items.map((item: any, idx: number) => (
                          <tr key={idx} className="border-b hover:bg-gray-50">
                            <td className="py-2 px-4">
                              {new Date(item.transaction_date).toLocaleDateString()}
                            </td>
                            <td className="py-2 px-4">{item.transaction_number}</td>
                            <td className="py-2 px-4 text-xs">{item.transaction_type}</td>
                            <td className="py-2 px-4 text-right">
                              {formatCurrency(item.amount_inclusive)}
                            </td>
                            <td className="py-2 px-4 text-right font-semibold text-red-600">
                              {formatCurrency(item.balance_due)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No open items</p>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

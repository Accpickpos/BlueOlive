'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Download } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';

const TRANSACTION_TYPES = [
  { value: 'INVOICE_STOCK', label: 'Invoice - Stock' },
  { value: 'INVOICE_EXPENSE', label: 'Invoice - Expense' },
  { value: 'CREDIT_STOCK', label: 'Credit Note - Stock' },
  { value: 'CREDIT_EXPENSE', label: 'Credit Note - Expense' },
  { value: 'PAYMENT', label: 'Payment' },
  { value: 'SETTLEMENT_DISCOUNT', label: 'Settlement Discount' },
  { value: 'DEBIT_JOURNAL', label: 'Debit Journal' },
  { value: 'CREDIT_JOURNAL', label: 'Credit Journal' },
];

export default function TransactionScroll({ onBack }: { onBack: () => void }) {
  const [startDate, setStartDate] = useState(
    new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [enquiryType, setEnquiryType] = useState<'scroll' | 'totals'>('scroll');
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [scrollData, setScrollData] = useState<any>(null);
  const [totalsData, setTotalsData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleTypeToggle = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('start_date', startDate);
      params.append('end_date', endDate);
      params.append('enquiry_type', enquiryType);

      selectedTypes.forEach((type) => {
        params.append('entry_types', type);
      });

      const response = await fetch(
        `${API_BASE_URL}/api/creditors/enquiries/transaction_scroll/?${params.toString()}`,
        {
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        if (enquiryType === 'scroll') {
          setScrollData(data);
          setTotalsData(null);
        } else {
          setTotalsData(data);
          setScrollData(null);
        }
      }
    } catch (err) {
      console.error('Error fetching transactions:', err);
    } finally {
      setLoading(false);
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
          <h1 className="text-3xl font-bold">Transaction Scroll</h1>
          <p className="text-gray-600">Detailed transaction listing and analysis</p>
        </div>
      </div>

      {/* Search Criteria */}
      <Card>
        <CardHeader>
          <CardTitle>Search Criteria</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Date Range */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium block mb-2">Start Date</label>
              <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium block mb-2">End Date</label>
              <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
            <div className="flex flex-col justify-end">
              <Button onClick={handleSearch} disabled={loading}>
                {loading ? 'Loading...' : 'Search'}
              </Button>
            </div>
          </div>

          {/* Enquiry Type */}
          <div>
            <label className="text-sm font-medium block mb-2">Enquiry Type</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="scroll"
                  checked={enquiryType === 'scroll'}
                  onChange={(e) => setEnquiryType(e.target.value as any)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Scroll (Detailed List)</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="totals"
                  checked={enquiryType === 'totals'}
                  onChange={(e) => setEnquiryType(e.target.value as any)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Totals (Summary)</span>
              </label>
            </div>
          </div>

          {/* Transaction Types */}
          <div>
            <label className="text-sm font-medium block mb-2">Transaction Types</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {TRANSACTION_TYPES.map((type) => (
                <label key={type.value} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(type.value)}
                    onChange={() => handleTypeToggle(type.value)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">{type.label}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {selectedTypes.length === 0
                ? 'Select transaction types to include, or leave blank for all'
                : `${selectedTypes.length} type(s) selected`}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Results - Scroll View */}
      {scrollData && enquiryType === 'scroll' && (
        <>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Transaction Scroll</CardTitle>
                <p className="text-sm text-gray-600 mt-1">
                  Period: {startDate} to {endDate} ({scrollData.count} transactions)
                </p>
              </div>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </CardHeader>
            <CardContent>
              {scrollData.transactions && scrollData.transactions.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left py-3 px-4 font-semibold">Date</th>
                        <th className="text-left py-3 px-4 font-semibold">Ref #</th>
                        <th className="text-left py-3 px-4 font-semibold">Type</th>
                        <th className="text-left py-3 px-4 font-semibold">Supplier</th>
                        <th className="text-right py-3 px-4 font-semibold">Net Amount</th>
                        <th className="text-right py-3 px-4 font-semibold">VAT</th>
                        <th className="text-right py-3 px-4 font-semibold">Total Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scrollData.transactions.map((txn: any, idx: number) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="py-2 px-4">
                            {new Date(txn.date).toLocaleDateString()}
                          </td>
                          <td className="py-2 px-4 font-mono text-xs">{txn.transaction_number}</td>
                          <td className="py-2 px-4 text-xs">{txn.transaction_type}</td>
                          <td className="py-2 px-4">{txn.supplier_name}</td>
                          <td className="text-right py-2 px-4">
                            {formatCurrency(txn.net_amount)}
                          </td>
                          <td className="text-right py-2 px-4">
                            {formatCurrency(txn.vat_amount)}
                          </td>
                          <td className="text-right py-2 px-4 font-semibold">
                            {formatCurrency(txn.total_amount)}
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

          {/* Grand Totals */}
          <Card>
            <CardHeader>
              <CardTitle>Grand Totals</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 bg-blue-50 rounded">
                  <p className="text-sm text-gray-600">Transaction Count</p>
                  <p className="text-2xl font-bold text-blue-700">{scrollData.grand_total?.count}</p>
                </div>
                <div className="p-4 bg-green-50 rounded">
                  <p className="text-sm text-gray-600">Total Net Amount</p>
                  <p className="text-2xl font-bold text-green-700">
                    {formatCurrency(scrollData.grand_total?.total_exclusive || 0)}
                  </p>
                </div>
                <div className="p-4 bg-orange-50 rounded">
                  <p className="text-sm text-gray-600">Total VAT</p>
                  <p className="text-2xl font-bold text-orange-700">
                    {formatCurrency(scrollData.grand_total?.total_vat || 0)}
                  </p>
                </div>
                <div className="p-4 bg-purple-50 rounded border-2 border-purple-300">
                  <p className="text-sm text-gray-600">Grand Total</p>
                  <p className="text-2xl font-bold text-purple-700">
                    {formatCurrency(scrollData.grand_total?.total_inclusive || 0)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Results - Totals View */}
      {totalsData && enquiryType === 'totals' && (
        <>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Transaction Totals Summary</CardTitle>
                <p className="text-sm text-gray-600 mt-1">
                  Period: {startDate} to {endDate}
                </p>
              </div>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </CardHeader>
            <CardContent>
              {totalsData.totals && totalsData.totals.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left py-3 px-4 font-semibold">Transaction Type</th>
                        <th className="text-right py-3 px-4 font-semibold">Count</th>
                        <th className="text-right py-3 px-4 font-semibold">Net Amount</th>
                        <th className="text-right py-3 px-4 font-semibold">VAT</th>
                        <th className="text-right py-3 px-4 font-semibold">Total Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {totalsData.totals.map((total: any, idx: number) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="py-2 px-4">{total.transaction_type}</td>
                          <td className="text-right py-2 px-4 font-semibold">{total.count}</td>
                          <td className="text-right py-2 px-4">
                            {formatCurrency(total.total_exclusive)}
                          </td>
                          <td className="text-right py-2 px-4">
                            {formatCurrency(total.total_vat)}
                          </td>
                          <td className="text-right py-2 px-4 font-semibold">
                            {formatCurrency(total.total_inclusive)}
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

          {/* Grand Totals */}
          <Card>
            <CardHeader>
              <CardTitle>Grand Totals</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 bg-blue-50 rounded">
                  <p className="text-sm text-gray-600">Total Transactions</p>
                  <p className="text-2xl font-bold text-blue-700">{totalsData.grand_total?.count}</p>
                </div>
                <div className="p-4 bg-green-50 rounded">
                  <p className="text-sm text-gray-600">Total Net Amount</p>
                  <p className="text-2xl font-bold text-green-700">
                    {formatCurrency(totalsData.grand_total?.total_exclusive || 0)}
                  </p>
                </div>
                <div className="p-4 bg-orange-50 rounded">
                  <p className="text-sm text-gray-600">Total VAT</p>
                  <p className="text-2xl font-bold text-orange-700">
                    {formatCurrency(totalsData.grand_total?.total_vat || 0)}
                  </p>
                </div>
                <div className="p-4 bg-purple-50 rounded border-2 border-purple-300">
                  <p className="text-sm text-gray-600">Grand Total</p>
                  <p className="text-2xl font-bold text-purple-700">
                    {formatCurrency(totalsData.grand_total?.total_inclusive || 0)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

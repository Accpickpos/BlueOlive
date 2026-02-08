'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ArrowLeft, Download } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';

interface SupplierData {
  account_number: number;
  account_name: string;
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
  status: string;
}

interface AgeAnalysisData {
  analysis: SupplierData[];
  totals: {
    current: number;
    '30_days': number;
    '60_days': number;
    '90_days': number;
    '120_days': number;
    '150_days': number;
    '180_days': number;
    total: number;
  };
  count: number;
}

interface ControlData {
  control_totals: {
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
    active_suppliers: number;
    total_suppliers: number;
  };
}

export default function CreditorsSummaryEnquiry({ onBack }: { onBack: () => void }) {
  const [enquiryType, setEnquiryType] = useState<'age' | 'control'>('age');
  const [orderBy, setOrderBy] = useState('A'); // A=name, N=number, V=value
  const [includeZero, setIncludeZero] = useState(true);
  const [ageData, setAgeData] = useState<AgeAnalysisData | null>(null);
  const [controlData, setControlData] = useState<ControlData | null>(null);
  const [loading, setLoading] = useState(false);
  const [sortByDisplay, setSortByDisplay] = useState('account_name'); // account_number, account_name, total

  const fetchAgeAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/creditors/enquiries/age_analysis/?order_by=${orderBy}&include_zero_balance=${includeZero}`,
        {
          credentials: 'include',
        }
      );
      if (response.ok) {
        const data = await response.json();
        setAgeData(data);
      }
    } catch (err) {
      console.error('Error fetching age analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchControlTotals = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/creditors/enquiries/control_enquiry/`,
        {
          credentials: 'include',
        }
      );
      if (response.ok) {
        const data = await response.json();
        setControlData(data);
      }
    } catch (err) {
      console.error('Error fetching control totals:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (enquiryType === 'age') {
      fetchAgeAnalysis();
    } else {
      fetchControlTotals();
    }
  }, [enquiryType, orderBy, includeZero]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
    }).format(value);
  };

  const getSortedData = (data: SupplierData[]) => {
    if (sortByDisplay === 'account_number') {
      return [...data].sort((a, b) => a.account_number - b.account_number);
    } else if (sortByDisplay === 'total') {
      return [...data].sort((a, b) => b.balances.total - a.balances.total);
    }
    return data;
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
          <h1 className="text-3xl font-bold">Total Creditors Summary</h1>
          <p className="text-gray-600">Age analysis and control enquiry for all creditors</p>
        </div>
      </div>

      {/* Enquiry Type Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Enquiry Type</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4 items-end">
            <div>
              <label className="text-sm font-medium block mb-2">Select Enquiry Type</label>
              <Select value={enquiryType} onValueChange={(value:string) => setEnquiryType(value as any)}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="age">Age Analysis</SelectItem>
                  <SelectItem value="control">Control Enquiry</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {enquiryType === 'age' && (
              <>
                <div>
                  <label className="text-sm font-medium block mb-2">Order By</label>
                  <Select value={orderBy} onValueChange={setOrderBy}>
                    <SelectTrigger className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="A">Account Name (A-Z)</SelectItem>
                      <SelectItem value="N">Account Number</SelectItem>
                      <SelectItem value="V">Value / Amount Outstanding</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeZero}
                    onChange={(e) => setIncludeZero(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">Include Zero Balances</span>
                </label>
              </>
            )}

            <Button onClick={() => (enquiryType === 'age' ? fetchAgeAnalysis() : fetchControlTotals())} disabled={loading}>
              {loading ? 'Loading...' : 'Refresh'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Age Analysis View */}
      {enquiryType === 'age' && ageData && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Total Suppliers</p>
                <p className="text-3xl font-bold">{ageData.count}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Total Outstanding</p>
                <p className="text-3xl font-bold">{formatCurrency(ageData.totals.total)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Current + 30 Days</p>
                <p className="text-3xl font-bold">
                  {formatCurrency(ageData.totals.current + ageData.totals['30_days'])}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Age Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Balance Breakdown by Ageing Period</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-8 gap-4">
                {[
                  { key: 'current' as const, label: 'Current' },
                  { key: '30_days' as const, label: '30 Days' },
                  { key: '60_days' as const, label: '60 Days' },
                  { key: '90_days' as const, label: '90 Days' },
                  { key: '120_days' as const, label: '120 Days' },
                  { key: '150_days' as const, label: '150 Days' },
                  { key: '180_days' as const, label: '180 Days' },
                  { key: 'total' as const, label: 'Total' },
                ].map((period) => (
                  <div key={period.key} className="text-center p-3 bg-gray-50 rounded">
                    <p className="text-xs text-gray-600">{period.label}</p>
                    <p className="text-sm font-bold">
                      {formatCurrency((ageData.totals as any)[period.key])}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Detailed Listing */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle>Creditors Listing</CardTitle>
              <div className="flex gap-2 items-center">
                <label className="text-sm font-medium">Sort By:</label>
                <Select value={sortByDisplay} onValueChange={setSortByDisplay}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="account_name">Account Name</SelectItem>
                    <SelectItem value="account_number">Account Number</SelectItem>
                    <SelectItem value="total">Total Due</SelectItem>
                  </SelectContent>
                </Select>
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Print
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50">
                      <th className="text-left py-3 px-4 font-semibold">Account #</th>
                      <th className="text-left py-3 px-4 font-semibold">Account Name</th>
                      <th className="text-right py-3 px-4 font-semibold">Current</th>
                      <th className="text-right py-3 px-4 font-semibold">30 Days</th>
                      <th className="text-right py-3 px-4 font-semibold">60 Days</th>
                      <th className="text-right py-3 px-4 font-semibold">90 Days</th>
                      <th className="text-right py-3 px-4 font-semibold">120+ Days</th>
                      <th className="text-right py-3 px-4 font-semibold">Total Due</th>
                      <th className="text-center py-3 px-4 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {getSortedData(ageData.analysis).map((supplier: SupplierData, idx: number) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="py-2 px-4">{supplier.account_number}</td>
                        <td className="py-2 px-4">{supplier.account_name}</td>
                        <td className="text-right py-2 px-4">
                          {formatCurrency(supplier.balances.current)}
                        </td>
                        <td className="text-right py-2 px-4">
                          {formatCurrency(supplier.balances['30_days'])}
                        </td>
                        <td className="text-right py-2 px-4">
                          {formatCurrency(supplier.balances['60_days'])}
                        </td>
                        <td className="text-right py-2 px-4">
                          {formatCurrency(supplier.balances['90_days'])}
                        </td>
                        <td className="text-right py-2 px-4">
                          {formatCurrency(
                            supplier.balances['120_days'] +
                              supplier.balances['150_days'] +
                              supplier.balances['180_days']
                          )}
                        </td>
                        <td className="text-right py-2 px-4 font-bold">
                          {formatCurrency(supplier.balances.total)}
                        </td>
                        <td className="text-center py-2 px-4">
                          <span
                            className={`text-xs px-2 py-1 rounded ${
                              supplier.status === 'Active'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {supplier.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t-2 bg-gray-50 font-bold">
                      <td colSpan={2} className="py-3 px-4">
                        TOTALS
                      </td>
                      <td className="text-right py-3 px-4">
                        {formatCurrency(ageData.totals.current)}
                      </td>
                      <td className="text-right py-3 px-4">
                        {formatCurrency(ageData.totals['30_days'])}
                      </td>
                      <td className="text-right py-3 px-4">
                        {formatCurrency(ageData.totals['60_days'])}
                      </td>
                      <td className="text-right py-3 px-4">
                        {formatCurrency(ageData.totals['90_days'])}
                      </td>
                      <td className="text-right py-3 px-4">
                        {formatCurrency(
                          ageData.totals['120_days'] +
                            ageData.totals['150_days'] +
                            ageData.totals['180_days']
                        )}
                      </td>
                      <td className="text-right py-3 px-4">
                        {formatCurrency(ageData.totals.total)}
                      </td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Control Enquiry View */}
      {enquiryType === 'control' && controlData && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Control Totals</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-8 gap-4">
                {[
                  { key: 'current' as const, label: 'Current' },
                  { key: '30_days' as const, label: '30 Days' },
                  { key: '60_days' as const, label: '60 Days' },
                  { key: '90_days' as const, label: '90 Days' },
                  { key: '120_days' as const, label: '120 Days' },
                  { key: '150_days' as const, label: '150 Days' },
                  { key: '180_days' as const, label: '180 Days' },
                  { key: 'total' as const, label: 'TOTAL' },
                ].map((period) => (
                  <div
                    key={period.key}
                    className={`p-4 rounded-lg ${
                      period.key === 'total'
                        ? 'bg-blue-100 border-2 border-blue-300'
                        : 'bg-gray-50'
                    }`}
                  >
                    <p className={`text-xs font-semibold ${period.key === 'total' ? 'text-blue-700' : 'text-gray-600'}`}>
                      {period.label}
                    </p>
                    <p className={`text-lg font-bold ${period.key === 'total' ? 'text-blue-700' : 'text-gray-900'}`}>
                      {formatCurrency((controlData.control_totals as any)[period.key])}
                    </p>
                  </div>
                ))}
              </div>

              <div className="border-t pt-6">
                <h3 className="font-semibold mb-4">Creditor Statistics</h3>
                <div className="grid grid-cols-2 gap-4">
                  <Card className="bg-green-50">
                    <CardContent className="pt-6">
                      <p className="text-sm text-gray-600">Active Suppliers</p>
                      <p className="text-3xl font-bold text-green-700">
                        {controlData.statistics.active_suppliers}
                      </p>
                    </CardContent>
                  </Card>
                  <Card className="bg-blue-50">
                    <CardContent className="pt-6">
                      <p className="text-sm text-gray-600">Total Suppliers</p>
                      <p className="text-3xl font-bold text-blue-700">
                        {controlData.statistics.total_suppliers}
                      </p>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

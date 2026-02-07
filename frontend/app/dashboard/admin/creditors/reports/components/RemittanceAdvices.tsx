'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Printer } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';

export default function RemittanceAdvices({ onBack }: { onBack: () => void }) {
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [periodType, setPeriodType] = useState('current');
  const [includeZero, setIncludeZero] = useState(false);
  const [sequence, setSequence] = useState('A');

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('period_type', periodType);
      params.append('include_zero', includeZero.toString());
      params.append('sequence', sequence);
      params.append('report_date', new Date().toISOString().split('T')[0]);

      const response = await fetch(
        `${API_BASE_URL}/api/creditors/reports/remittance_advices/?${params.toString()}`,
        {
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        setReportData(data);
      }
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(value);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Remittance Advices</h1>
          <p className="text-gray-600">Print remittance statements for suppliers</p>
        </div>
      </div>

      {!reportData ? (
        <Card>
          <CardHeader>
            <CardTitle>Report Options</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Period Type</label>
                <select
                  value={periodType}
                  onChange={(e) => setPeriodType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                >
                  <option value="current">Current Period</option>
                  <option value="historical">Historical Periods</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium">Sequence</label>
                <select
                  value={sequence}
                  onChange={(e) => setSequence(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                >
                  <option value="A">Alphabetical</option>
                  <option value="N">Numerical</option>
                </select>
              </div>
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

            <Button onClick={handleGenerate} disabled={loading} className="bg-green-600 hover:bg-green-700">
              {loading ? 'Generating...' : 'Generate Remittances'}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold">{reportData.report_title}</h2>
              <p className="text-gray-600 text-sm">Total: {reportData.total_remittances} suppliers</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => window.print()}>
                <Printer className="w-4 h-4 mr-2" /> Print
              </Button>
              <Button variant="outline" onClick={() => setReportData(null)}>
                Generate New Report
              </Button>
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Remittance Listings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100 border-b">
                    <tr>
                      <th className="text-left p-2">Account #</th>
                      <th className="text-left p-2">Name</th>
                      <th className="text-right p-2">Current</th>
                      <th className="text-right p-2">Total Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.remittances?.map((item: any) => (
                      <tr key={item.supplier_id} className="border-b hover:bg-gray-50">
                        <td className="p-2">{item.supplier_id}</td>
                        <td className="p-2 font-medium">{item.supplier_name}</td>
                        <td className="text-right p-2">{formatCurrency(item.balances.current)}</td>
                        <td className="text-right p-2 font-semibold">{formatCurrency(item.balances.total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

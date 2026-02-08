'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Download, Printer } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';

interface Account {
  account_number: number;
  name: string;
  short_name: string;
  account_type: string;
  contact_person: string;
  telephone1: string;
  telephone2: string;
  email: string;
  fax: string;
  postal_address?: Record<string, any>;
  physical_address?: Record<string, any>;
  banking_details?: Record<string, any>;
}

interface ReportData {
  report_title: string;
  report_date: string;
  sequence: string;
  address_type: string;
  include_banking_details: boolean;
  total_accounts: number;
  accounts: Account[];
}

export default function AccountDetailsReport({ onBack }: { onBack: () => void }) {
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [includeBanking, setIncludeBanking] = useState(false);
  const [sequence, setSequence] = useState('A');
  const [addressType, setAddressType] = useState('both');
  const [includePostal, setIncludePostal] = useState(true);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('include_postal', includePostal.toString());
      params.append('address_type', addressType);
      params.append('sequence', sequence);
      params.append('include_banking', includeBanking.toString());

      const response = await fetch(
        `${API_BASE_URL}/api/creditors/reports/account_details/?${params.toString()}`,
        {
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        setReportData(data);
      }
    } catch (err) {
      console.error('Error generating report:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number | undefined) => {
    if (!value) return '-';
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
          <h1 className="text-3xl font-bold">Account Details Report</h1>
          <p className="text-gray-600">List all creditors with detailed information</p>
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
                <label className="text-sm font-medium">Address Type</label>
                <select
                  value={addressType}
                  onChange={(e) => setAddressType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                >
                  <option value="both">Both (Postal & Physical)</option>
                  <option value="postal">Postal Address Only</option>
                  <option value="delivery">Physical Address Only</option>
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

            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includePostal}
                  onChange={(e) => setIncludePostal(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Include Postal/Delivery Addresses</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeBanking}
                  onChange={(e) => setIncludeBanking(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Include Banking Details</span>
              </label>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleGenerate} disabled={loading} className="bg-blue-600 hover:bg-blue-700">
                {loading ? 'Generating...' : 'Generate Report'}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Report Header */}
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold">{reportData.report_title}</h2>
              <p className="text-gray-600 text-sm mt-1">
                Date: {reportData.report_date} | Sequence: {reportData.sequence} | Total Accounts: {reportData.total_accounts}
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => window.print()}>
                <Printer className="w-4 h-4 mr-2" />
                Print
              </Button>
              <Button variant="outline" onClick={() => setReportData(null)}>
                Generate New Report
              </Button>
            </div>
          </div>

          {/* Accounts Table */}
          <Card>
            <CardHeader>
              <CardTitle>Account Listing</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100 border-b">
                    <tr>
                      <th className="text-left p-2">Account #</th>
                      <th className="text-left p-2">Name</th>
                      <th className="text-left p-2">Contact</th>
                      <th className="text-left p-2">Telephone</th>
                      <th className="text-left p-2">Email</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.accounts.map((account) => (
                      <tr key={account.account_number} className="border-b hover:bg-gray-50">
                        <td className="p-2">{account.account_number}</td>
                        <td className="p-2 font-medium">{account.name}</td>
                        <td className="p-2">{account.contact_person}</td>
                        <td className="p-2">{account.telephone1}</td>
                        <td className="p-2">{account.email}</td>
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

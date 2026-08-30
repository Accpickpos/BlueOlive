'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { glMasterApi } from '@/lib/general-ledger';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Loader2, Search } from 'lucide-react';
import Link from 'next/link';

export default function AccountHistoryEnquiryPage() {
  const [accountId, setAccountId] = useState('');
  const [submittedId, setSubmittedId] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['gl-account-history', submittedId],
    queryFn: () => glMasterApi.accountHistory(submittedId as string),
    enabled: submittedId !== null,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/general-ledger/enquiries">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Account History</h1>
          <p className="text-gray-600 mt-1">Period, budget, and prior-year history for one account</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex gap-2 max-w-md">
          <Input
            type="number"
            placeholder="GLMast record ID"
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
          />
          <Button onClick={() => setSubmittedId(accountId)} disabled={!accountId}>
            <Search className="w-4 h-4 mr-2" />
            Search
          </Button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Enter the account's internal ID (visible on the Chart of Accounts list).
        </p>
      </Card>

      {isLoading && (
        <div className="flex justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      )}

      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 text-sm">
          Account not found.
        </div>
      )}

      {data && (
        <div className="space-y-4">
          <Card className="p-6">
            <h2 className="text-lg font-bold">
              {data.account} — {data.name}
            </h2>
            <p className="text-sm text-gray-600">
              {data.type} · {data.drorcr} · Balance B/F: {data.balbfwd?.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}
            </p>
          </Card>

          <Card className="p-6">
            <h3 className="font-bold mb-3">Periods</h3>
            <div className="grid grid-cols-4 md:grid-cols-7 gap-3 text-sm">
              {data.periods?.map((p: { period: number; balance: number }) => (
                <div key={p.period} className="border rounded p-2 text-center">
                  <p className="text-gray-500 text-xs">P{p.period}</p>
                  <p className="font-medium">{p.balance.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="font-bold mb-3">Budgets</h3>
            <div className="grid grid-cols-4 md:grid-cols-6 gap-3 text-sm">
              {data.budgets?.map((p: { period: number; budget: number }) => (
                <div key={p.period} className="border rounded p-2 text-center">
                  <p className="text-gray-500 text-xs">P{p.period}</p>
                  <p className="font-medium">{p.budget.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="font-bold mb-3">Last Year</h3>
            <div className="grid grid-cols-4 md:grid-cols-6 gap-3 text-sm">
              {data.last_year?.map((p: { period: number; last_year: number }) => (
                <div key={p.period} className="border rounded p-2 text-center">
                  <p className="text-gray-500 text-xs">P{p.period}</p>
                  <p className="font-medium">{p.last_year.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

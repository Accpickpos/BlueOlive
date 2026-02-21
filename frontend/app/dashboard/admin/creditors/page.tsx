'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader, Plus, Receipt, RotateCcw, FileText, Zap } from 'lucide-react';
import Link from 'next/link';

export default function CreditorsOverviewPage() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['creditors-summary'],
    queryFn: () => creditorsApi.summary.get(),
    staleTime: 5 * 60 * 1000,
  });

  const { data: ageData } = useQuery({
    queryKey: ['creditors-age-analysis'],
    queryFn: () => creditorsApi.summary.ageAnalysis({ include_zero_balance: false }),
    staleTime: 5 * 60 * 1000,
  });

  const { data: recentActivity } = useQuery({
    queryKey: ['creditors-recent-activity'],
    queryFn: () => creditorsApi.ledger.list({ ordering: '-transaction_date', page_size: 5 }),
  });

  // Calculate summary from age analysis data
  const calculatedSummary = ageData ? ageData.reduce(
    (acc, creditor) => ({
      totalPayable: acc.totalPayable + creditor.total_outstanding_balance,
      current: acc.current + creditor.balance_current,
      days30to60: acc.days30to60 + creditor.balance_30_days,
      days60to90: acc.days60to90 + creditor.balance_60_days,
      days90Plus: acc.days90Plus + creditor.balance_90_days + creditor.balance_120_days + creditor.balance_150_days + creditor.balance_180_days,
      count: acc.count + 1,
    }),
    { totalPayable: 0, current: 0, days30to60: 0, days60to90: 0, days90Plus: 0, count: 0 }
  ) : null;

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Creditors Management</h1>
        <p className="text-gray-600 mt-1">Manage supplier accounts, transactions, and payments</p>
      </div>

      {/* Summary Cards */}
      {calculatedSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-6">
            <p className="text-xs text-gray-600 uppercase">Total Outstanding</p>
            <p className="text-3xl font-bold text-red-600 mt-2">
              R {calculatedSummary.totalPayable.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
            </p>
            <p className="text-xs text-gray-500 mt-2">{calculatedSummary.count} suppliers</p>
          </Card>

          <Card className="p-6 border-l-4 border-l-green-500">
            <p className="text-xs text-gray-600 uppercase">Current</p>
            <p className="text-2xl font-bold text-green-600 mt-2">
              R {calculatedSummary.current.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
            </p>
          </Card>

          <Card className="p-6 border-l-4 border-l-amber-500">
            <p className="text-xs text-gray-600 uppercase">30-90 Days</p>
            <p className="text-2xl font-bold text-amber-600 mt-2">
              R {(calculatedSummary.days30to60 + calculatedSummary.days60to90).toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
            </p>
          </Card>

          <Card className="p-6 border-l-4 border-l-red-500">
            <p className="text-xs text-gray-600 uppercase">90+ Days Overdue</p>
            <p className="text-2xl font-bold text-red-600 mt-2">
              R {calculatedSummary.days90Plus.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
            </p>
          </Card>
        </div>
      )}

      {/* Quick Action Buttons */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
        <Link href="/dashboard/admin/creditors/transactions/stock-receipts">
          <Button className="w-full bg-blue-600 hover:bg-blue-700 flex flex-col gap-2 h-auto py-4">
            <Receipt className="w-5 h-5" />
            <span className="text-xs">Stock Receipt</span>
          </Button>
        </Link>
        <Link href="/dashboard/admin/creditors/transactions/invoices/expense">
          <Button className="w-full bg-purple-600 hover:bg-purple-700 flex flex-col gap-2 h-auto py-4">
            <FileText className="w-5 h-5" />
            <span className="text-xs">Invoice</span>
          </Button>
        </Link>
        <Link href="/dashboard/admin/creditors/transactions/payments">
          <Button className="w-full bg-green-600 hover:bg-green-700 flex flex-col gap-2 h-auto py-4">
            <Plus className="w-5 h-5" />
            <span className="text-xs">Payment</span>
          </Button>
        </Link>
        <Link href="/dashboard/admin/creditors/transactions/rfc">
          <Button className="w-full bg-orange-600 hover:bg-orange-700 flex flex-col gap-2 h-auto py-4">
            <RotateCcw className="w-5 h-5" />
            <span className="text-xs">RFC</span>
          </Button>
        </Link>
        <Link href="/dashboard/admin/creditors/transactions/journals">
          <Button className="w-full bg-indigo-600 hover:bg-indigo-700 flex flex-col gap-2 h-auto py-4">
            <Zap className="w-5 h-5" />
            <span className="text-xs">Journal</span>
          </Button>
        </Link>
        <Link href="/dashboard/admin/creditors/maintenance/accounts">
          <Button className="w-full bg-gray-600 hover:bg-gray-700 flex flex-col gap-2 h-auto py-4">
            <Plus className="w-5 h-5" />
            <span className="text-xs">New Account</span>
          </Button>
        </Link>
      </div>

      {/* Recent Activity */}
      {recentActivity?.results && recentActivity.results.length > 0 && (
        <Card className="p-6">
          <h2 className="text-lg font-bold mb-4">Recent Activity</h2>
          <div className="space-y-3">
            {recentActivity.results.map((transaction: any) => (
              <div key={transaction.id} className="flex items-center justify-between py-2 border-b last:border-b-0">
                <div>
                  <p className="font-medium">{transaction.creditor_name}</p>
                  <p className="text-xs text-gray-600">{new Date(transaction.transaction_date).toLocaleDateString('en-ZA')}</p>
                </div>
                <p className="font-bold text-right">
                  R {transaction.total_amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

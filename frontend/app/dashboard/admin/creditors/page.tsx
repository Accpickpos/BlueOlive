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

  const { data: recentActivity } = useQuery({
    queryKey: ['creditors-recent-activity'],
    queryFn: () => creditorsApi.transactions.list({ ordering: '-date', page_size: 5 }),
  });

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
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-6">
            <p className="text-xs text-gray-600 uppercase">Total Outstanding</p>
            <p className="text-3xl font-bold text-red-600 mt-2">
              R {summary.total_payable?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
            </p>
            <p className="text-xs text-gray-500 mt-2">{summary.total_creditors} suppliers</p>
          </Card>

          <Card className="p-6 border-l-4 border-l-green-500">
            <p className="text-xs text-gray-600 uppercase">Current</p>
            <p className="text-2xl font-bold text-green-600 mt-2">
              R {summary.current_aging?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
            </p>
          </Card>

          <Card className="p-6 border-l-4 border-l-amber-500">
            <p className="text-xs text-gray-600 uppercase">30-90 Days</p>
            <p className="text-2xl font-bold text-amber-600 mt-2">
              R {((summary.d30 || 0) + (summary.d60 || 0) + (summary.d90 || 0))?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
            </p>
          </Card>

          <Card className="p-6 border-l-4 border-l-red-500">
            <p className="text-xs text-gray-600 uppercase">90+ Days Overdue</p>
            <p className="text-2xl font-bold text-red-600 mt-2">
              R {summary.critical_aging?.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
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
                  <p className="font-medium">{transaction.supplier_name}</p>
                  <p className="text-xs text-gray-600">{new Date(transaction.date).toLocaleDateString('en-ZA')}</p>
                </div>
                <p className="font-bold text-right">
                  R {transaction.amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

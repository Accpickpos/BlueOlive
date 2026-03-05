'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader, ChevronLeft } from 'lucide-react';
import Link from 'next/link';

export default function CreditorAccountDetailPage() {
  const params = useParams();
  const accountId = params.id as string;
  const [page, setPage] = useState(1);
  const accountIdNum = parseInt(accountId, 10);

  const { data: account, isLoading } = useQuery({
    queryKey: ['creditor-account', accountId],
    queryFn: () => creditorsApi.accounts.get(accountIdNum),
  });

  const { data: transactions } = useQuery({
    queryKey: ['account-transactions', accountId, page],
    queryFn: () =>
      creditorsApi.transactions.list({
        creditor: accountIdNum,
        page,
        page_size: 25,
        ordering: '-transaction_date',
      }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!account) {
    return <div className="text-center py-8 text-gray-500">Account not found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/creditors/enquiries">
          <Button variant="outline" size="sm" className="gap-2">
            <ChevronLeft className="w-4 h-4" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">{account.name}</h1>
          <p className="text-gray-600 mt-1">Account: {account.supplier_number}</p>
        </div>
      </div>

      {/* Account Details Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6">
          <p className="text-xs text-gray-600 uppercase">Account Balance</p>
          <p className="text-2xl font-bold text-red-600 mt-2">
            R {account.total_outstanding_balance?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
          </p>
        </Card>
        <Card className="p-6 border-l-4 border-l-green-500">
          <p className="text-xs text-gray-600 uppercase">Current</p>
          <p className="text-2xl font-bold text-green-600 mt-2">
            R {account.balance_current?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
          </p>
        </Card>
        <Card className="p-6 border-l-4 border-l-amber-500">
          <p className="text-xs text-gray-600 uppercase">30-60 Days</p>
          <p className="text-2xl font-bold text-amber-600 mt-2">
            R {((account.balance_30_days || 0) + (account.balance_60_days || 0))?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
          </p>
        </Card>
        <Card className="p-6 border-l-4 border-l-red-500">
          <p className="text-xs text-gray-600 uppercase">90+ Days</p>
          <p className="text-2xl font-bold text-red-600 mt-2">
            R {((account.balance_90_days || 0) + (account.balance_120_days || 0))?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
          </p>
        </Card>
      </div>

      {/* Account Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="font-bold mb-4">Account Information</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Account Type:</span>
              <span className="font-bold">{account.account_category}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Contact Person:</span>
              <span className="font-bold">{account.contact_person || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Telephone:</span>
              <span className="font-bold">{account.telephone || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Email:</span>
              <span className="font-bold">{account.email || 'N/A'}</span>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <h2 className="font-bold mb-4">Trade Terms</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Credit Terms:</span>
              <span className="font-bold">{account.payment_terms_days} days</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Payment Discount:</span>
              <span className="font-bold">{account.prompt_payment_discount_percent}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Last Payment:</span>
              <span className="font-bold">
                {account.last_paid_date
                  ? new Date(account.last_paid_date).toLocaleDateString('en-ZA')
                  : 'N/A'}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Transaction History */}
      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Transaction History</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Date</th>
                <th className="px-4 py-3 text-left font-semibold">Reference</th>
                <th className="px-4 py-3 text-left font-semibold">Type</th>
                <th className="px-4 py-3 text-left font-semibold">Description</th>
                <th className="px-4 py-3 text-right font-semibold">Amount</th>
              </tr>
            </thead>
            <tbody>
              {transactions?.results?.map((txn: any) => (
                <tr key={txn.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">
                    {new Date(txn.transaction_date).toLocaleDateString('en-ZA')}
                  </td>
                  <td className="px-4 py-3 font-medium">{txn.reference_number}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      {txn.transaction_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{txn.description}</td>
                  <td className="px-4 py-3 text-right font-bold">
                    R {txn.amount?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t">
          <p className="text-sm text-gray-600">
            Showing {transactions?.results?.length || 0} of {transactions?.count || 0} transactions
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={!transactions?.previous}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={!transactions?.next}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

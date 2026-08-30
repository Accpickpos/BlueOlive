'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { glParametersApi } from '@/lib/general-ledger';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader, BookOpen, FolderKanban, Search, BarChart3, AlertTriangle } from 'lucide-react';

export default function GeneralLedgerOverviewPage() {
  const { data: status, isLoading } = useQuery({
    queryKey: ['gl-system-status'],
    queryFn: () => glParametersApi.systemStatus(),
    staleTime: 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">General Ledger</h1>
        <p className="text-gray-600 mt-1">Chart of accounts, journal posting, standing journals, and financial reports</p>
      </div>

      {status && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-6">
            <p className="text-xs text-gray-600 uppercase">Current Period</p>
            <p className="text-3xl font-bold mt-2">{status.curperiod}</p>
            <p className="text-xs text-gray-500 mt-2">Year {status.currentyr}</p>
          </Card>

          <Card className={`p-6 border-l-4 ${status.outstanding_batches > 0 ? 'border-l-amber-500' : 'border-l-green-500'}`}>
            <p className="text-xs text-gray-600 uppercase">Outstanding Batches</p>
            <p className={`text-3xl font-bold mt-2 ${status.outstanding_batches > 0 ? 'text-amber-600' : 'text-green-600'}`}>
              {status.outstanding_batches}
            </p>
            {status.outstanding_batches > 0 && (
              <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Must be posted before Period/Year End
              </p>
            )}
          </Card>

          <Card className="p-6">
            <p className="text-xs text-gray-600 uppercase">Next Batch Number</p>
            <p className="text-3xl font-bold mt-2">{status.next_batchno}</p>
          </Card>

          <Card className="p-6">
            <p className="text-xs text-gray-600 uppercase">Last Transaction</p>
            <p className="text-lg font-bold mt-2">
              {status.last_transaction_date
                ? new Date(status.last_transaction_date).toLocaleDateString('en-ZA')
                : '—'}
            </p>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Link href="/dashboard/admin/general-ledger/maintenance">
          <Button className="w-full bg-blue-600 hover:bg-blue-700 flex flex-col gap-2 h-auto py-4">
            <BookOpen className="w-5 h-5" />
            <span className="text-xs">Maintenance</span>
          </Button>
        </Link>
        <Link href="/dashboard/admin/general-ledger/transactions">
          <Button className="w-full bg-purple-600 hover:bg-purple-700 flex flex-col gap-2 h-auto py-4">
            <FolderKanban className="w-5 h-5" />
            <span className="text-xs">Transactions</span>
          </Button>
        </Link>
        <Link href="/dashboard/admin/general-ledger/enquiries">
          <Button className="w-full bg-green-600 hover:bg-green-700 flex flex-col gap-2 h-auto py-4">
            <Search className="w-5 h-5" />
            <span className="text-xs">Enquiries</span>
          </Button>
        </Link>
        <Link href="/dashboard/admin/general-ledger/reports">
          <Button className="w-full bg-orange-600 hover:bg-orange-700 flex flex-col gap-2 h-auto py-4">
            <BarChart3 className="w-5 h-5" />
            <span className="text-xs">Reports</span>
          </Button>
        </Link>
      </div>
    </div>
  );
}

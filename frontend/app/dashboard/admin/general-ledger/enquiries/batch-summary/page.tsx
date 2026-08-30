'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { glTransactionsApi } from '@/lib/general-ledger';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Loader2, Search } from 'lucide-react';
import Link from 'next/link';

export default function BatchSummaryEnquiryPage() {
  const [batchno, setBatchno] = useState('');
  const [submitted, setSubmitted] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['gl-batch-summary-enquiry', submitted],
    queryFn: () => glTransactionsApi.batchSummary(submitted as string),
    enabled: submitted !== null,
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
          <h1 className="text-3xl font-bold">Batch Summary</h1>
          <p className="text-gray-600 mt-1">Posted GL batch totals and status</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex gap-2 max-w-md">
          <Input
            type="number"
            placeholder="Batch number"
            value={batchno}
            onChange={(e) => setBatchno(e.target.value)}
          />
          <Button onClick={() => setSubmitted(batchno)} disabled={!batchno}>
            <Search className="w-4 h-4 mr-2" />
            Search
          </Button>
        </div>
      </Card>

      {isLoading && (
        <div className="flex justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      )}

      {data && data.status === 'no_data' && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-gray-600 text-sm">
          {data.message}
        </div>
      )}

      {data && data.transaction_count !== undefined && (
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">Batch {data.batchno}</h2>
            <Badge variant={data.is_balanced ? 'default' : 'destructive'}>
              {data.is_balanced ? 'Balanced' : 'Unbalanced'}
            </Badge>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Transactions</p>
              <p className="font-bold">{data.transaction_count}</p>
            </div>
            <div>
              <p className="text-gray-500">Total Debits</p>
              <p className="font-bold">{data.total_debits.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</p>
            </div>
            <div>
              <p className="text-gray-500">Total Credits</p>
              <p className="font-bold">{data.total_credits.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</p>
            </div>
            <div>
              <p className="text-gray-500">Net Balance</p>
              <p className="font-bold">{data.net_balance.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</p>
            </div>
          </div>
          <div className="text-sm text-gray-600">
            {data.date_range?.earliest} – {data.date_range?.latest}
          </div>
        </Card>
      )}
    </div>
  );
}

'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import PostDatedChequeForm from '@/components/debtors/forms/PostDatedChequeForm';
import type { PostDatedCheque } from '@/lib/types/debtors';
import { Badge } from '@/components/ui/badge';
import { AlertCircle } from 'lucide-react';

export default function PDCPage() {
  const [debtorId, setDebtorId] = useState<number | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const { data: pdcs, isLoading } = useQuery({
    queryKey: ['pdcs', debtorId, refreshTrigger],
    queryFn: () => debtorsApi.pdcs.list(debtorId || undefined),
    staleTime: 2 * 60 * 1000,
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OUTSTANDING':
        return 'bg-orange-500';
      case 'RECEIVED':
        return 'bg-blue-500';
      case 'CLEARED':
        return 'bg-green-500';
      case 'DISHONOURED':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const handleStatusChange = async (pdc: PostDatedCheque, newStatus: string) => {
    if (window.confirm(`Update PDC status to ${newStatus}?`)) {
      try {
        await debtorsApi.pdcs.updateStatus(
          pdc.id,
          newStatus as any,
          new Date().toISOString().split('T')[0]
        );
        setRefreshTrigger((prev) => prev + 1);
      } catch (err) {
        console.error('Update failed:', err);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Post-Dated Cheques (PDC)</h1>
        <p className="text-gray-600 mt-1">Track and manage post-dated cheques from customers</p>
      </div>

      {/* Add New PDC */}
      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Record New PDC</h2>
        <PostDatedChequeForm onSuccess={() => setRefreshTrigger((prev) => prev + 1)} />
      </Card>

      {/* PDC List */}
      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">PDC Register</h2>

        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Filter by Debtor (Optional)</label>
          <Input
            type="number"
            placeholder="Enter debtor ID to filter"
            onChange={(e) => setDebtorId(e.target.value ? parseInt(e.target.value) : null)}
          />
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-gray-600">Loading cheques...</div>
        ) : (pdcs?.results?.length || 0) === 0 ? (
          <div className="text-center py-8 text-gray-600">No PDCs found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Debtor</th>
                  <th className="px-4 py-3 text-left font-semibold">Cheque #</th>
                  <th className="px-4 py-3 text-left font-semibold">Bank</th>
                  <th className="px-4 py-3 text-right font-semibold">Amount</th>
                  <th className="px-4 py-3 text-left font-semibold">Expected Date</th>
                  <th className="px-4 py-3 text-left font-semibold">Status</th>
                  <th className="px-4 py-3 text-center font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {pdcs?.results?.map((pdc: PostDatedCheque) => (
                  <tr key={pdc.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3">{pdc.debtor_id}</td>
                    <td className="px-4 py-3 font-medium">{pdc.cheque_number}</td>
                    <td className="px-4 py-3">{pdc.bank || '-'}</td>
                    <td className="px-4 py-3 text-right font-semibold">
                      ${pdc.amount?.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3">
                      {new Date(pdc.expected_date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={getStatusColor(pdc.status)}>
                        {pdc.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <select
                        className="text-xs border rounded px-2 py-1"
                        value={pdc.status}
                        onChange={(e) => handleStatusChange(pdc, e.target.value)}
                      >
                        <option value={pdc.status}>Select action...</option>
                        {pdc.status === 'OUTSTANDING' && (
                          <>
                            <option value="RECEIVED">Mark Received</option>
                            <option value="DISHONOURED">Mark Dishonoured</option>
                          </>
                        )}
                        {pdc.status === 'RECEIVED' && <option value="CLEARED">Mark Cleared</option>}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

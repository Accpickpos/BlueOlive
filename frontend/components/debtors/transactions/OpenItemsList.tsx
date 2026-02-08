'use client';

import { useQuery, useMutation } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { OpenItem } from '@/lib/types/debtors';
import { useState } from 'react';
import { Loader } from 'lucide-react';

interface OpenItemsListProps {
  debtorId: number;
  refreshTrigger: number;
}

export default function OpenItemsList({ debtorId, refreshTrigger }: OpenItemsListProps) {
  const { data: openItems, isLoading } = useQuery({
    queryKey: ['open-items', debtorId, refreshTrigger],
    queryFn: () => debtorsApi.openItems.list(debtorId),
    enabled: !!debtorId,
  });

  const [receiptAmount, setReceiptAmount] = useState('');
  const [selectedItems, setSelectedItems] = useState<{ [key: number]: number }>({});

  const allocateMutation = useMutation({
    mutationFn: async () => {
      return debtorsApi.openItems.allocate({
        debtor_id: debtorId,
        receipt_amount: parseFloat(receiptAmount),
        allocations: Object.entries(selectedItems).map(([itemId, amount]) => ({
          open_item_id: parseInt(itemId),
          amount,
        })),
      });
    },
  });

  const handleAllocationChange = (itemId: number, amount: number) => {
    setSelectedItems((prev) => ({
      ...prev,
      [itemId]: amount,
    }));
  };

  const handleAllocate = async () => {
    if (Object.keys(selectedItems).length === 0 || !receiptAmount) {
      alert('Please select items and enter receipt amount');
      return;
    }
    allocateMutation.mutate();
  };

  if (isLoading) {
    return <div className="text-center py-6">Loading open items...</div>;
  }

  const items = openItems?.results || [];

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-2">Receipt Amount</label>
        <Input
          type="number"
          step="0.01"
          value={receiptAmount}
          onChange={(e) => setReceiptAmount(e.target.value)}
          placeholder="Enter receipt amount"
        />
      </div>

      {items.length === 0 ? (
        <div className="text-center py-6 text-gray-600">No open items for this debtor</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Document</th>
                <th className="px-4 py-3 text-left font-semibold">Date</th>
                <th className="px-4 py-3 text-right font-semibold">Amount</th>
                <th className="px-4 py-3 text-right font-semibold">Outstanding</th>
                <th className="px-4 py-3 text-right font-semibold">Allocate</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item: OpenItem) => (
                <tr key={item.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3">{item.document_number || `Doc ${item.id}`}</td>
                  <td className="px-4 py-3">{new Date(item.document_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-right">${item.amount?.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                  <td className="px-4 py-3 text-right font-semibold">${item.outstanding?.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                  <td className="px-4 py-3 text-right">
                    <input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      className="w-20 border rounded px-2 py-1 text-right"
                      onChange={(e) => handleAllocationChange(item.id, parseFloat(e.target.value) || 0)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Button
        onClick={handleAllocate}
        disabled={allocateMutation.isPending || Object.keys(selectedItems).length === 0}
        className="bg-green-600 hover:bg-green-700"
      >
        {allocateMutation.isPending && <Loader className="w-4 h-4 mr-2 animate-spin" />}
        Allocate Receipt
      </Button>
    </div>
  );
}

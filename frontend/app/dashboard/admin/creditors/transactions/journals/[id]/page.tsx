'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader } from 'lucide-react';

export default function JournalEntryForm() {
  const router = useRouter();
  const params = useParams();
  const entryId = params.id as string;
  const isNew = entryId === 'new';

  const [formData, setFormData] = useState({
    supplier_id: 0,
    entry_date: new Date().toISOString().split('T')[0],
    entry_type: 'DEBIT',
    description: '',
    amount: 0,
    reference: '',
  });

  const { data: suppliers } = useQuery({
    queryKey: ['creditors-accounts'],
    queryFn: () => creditorsApi.accounts.list({ page_size: 500 }),
  });

  const { data: entry, isLoading } = useQuery({
    queryKey: ['journal-entry', entryId],
    queryFn: () => creditorsApi.transactions.get(entryId),
    enabled: !isNew,
  });

  const mutation = useMutation({
    mutationFn: (data: any) =>
      isNew
        ? creditorsApi.transactions.create({ ...data, transaction_type: 'JOURNAL' })
        : creditorsApi.transactions.update(entryId, data),
    onSuccess: () => {
      router.push('/dashboard/admin/creditors/transactions/journals');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">{isNew ? 'New Journal Entry' : 'Edit Journal Entry'}</h1>
        <p className="text-gray-600 mt-1">Record an adjustment or correction to a creditor account</p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Entry Details */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Entry Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Creditor Account</label>
              <select
                value={formData.supplier_id}
                onChange={(e) => setFormData({ ...formData, supplier_id: parseInt(e.target.value) })}
                className="w-full border border-gray-300 rounded px-3 py-2"
                required
              >
                <option value={0}>Select Account...</option>
                {suppliers?.results?.map((supplier: any) => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.account_number} - {supplier.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Entry Date</label>
              <Input
                type="date"
                value={formData.entry_date}
                onChange={(e) => setFormData({ ...formData, entry_date: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Entry Type</label>
              <select
                value={formData.entry_type}
                onChange={(e) => setFormData({ ...formData, entry_type: e.target.value })}
                className="w-full border border-gray-300 rounded px-3 py-2"
                required
              >
                <option value="DEBIT">Debit (Increase Payable)</option>
                <option value="CREDIT">Credit (Reduce Payable)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Reference</label>
              <Input
                type="text"
                value={formData.reference}
                onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                placeholder="e.g., Correction, Adjustment"
              />
            </div>
          </div>
        </Card>

        {/* Amount & Description */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Amount & Description</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Amount (R)</label>
              <Input
                type="number"
                step="0.01"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                placeholder="0.00"
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 mt-4">
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full border border-gray-300 rounded px-3 py-2"
                rows={3}
                placeholder="Reason for the journal entry"
                required
              />
            </div>
          </div>
        </Card>

        {/* Summary */}
        {formData.amount > 0 && (
          <Card className="p-6 mb-6 bg-gray-50">
            <h3 className="font-bold mb-3">Entry Summary</h3>
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600 mb-1">Entry Type: <strong>{formData.entry_type}</strong></p>
                <p className="text-sm text-gray-600">Amount: <strong>R {formData.amount.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}</strong></p>
              </div>
              <div className={`px-4 py-2 rounded ${
                formData.entry_type === 'DEBIT' 
                  ? 'bg-red-100 text-red-800' 
                  : 'bg-green-100 text-green-800'
              }`}>
                <p className="text-sm font-bold">{formData.entry_type === 'DEBIT' ? 'PAYABLE ↑' : 'PAYABLE ↓'}</p>
              </div>
            </div>
          </Card>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700"
            disabled={mutation.isPending}
          >
            {mutation.isPending ? 'Saving...' : 'Save Entry'}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}

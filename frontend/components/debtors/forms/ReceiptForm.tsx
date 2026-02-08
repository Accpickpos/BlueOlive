'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, AlertCircle, CheckCircle } from 'lucide-react';

interface ReceiptFormProps {
  onSuccess?: () => void;
}

export default function ReceiptForm({ onSuccess }: ReceiptFormProps) {
  const [formData, setFormData] = useState({
    debtor_id: '',
    amount: '',
    reference_number: '',
    transaction_date: new Date().toISOString().split('T')[0],
  });

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!formData.debtor_id || !formData.amount) {
        throw new Error('Debtor ID and amount are required');
      }
      return debtorsApi.transactions.postReceipt({
        debtor_id: parseInt(formData.debtor_id),
        amount: parseFloat(formData.amount),
        reference_number: formData.reference_number || undefined,
        transaction_date: formData.transaction_date,
      });
    },
    onSuccess: () => {
      setSuccess(true);
      setFormData({
        debtor_id: '',
        amount: '',
        reference_number: '',
        transaction_date: new Date().toISOString().split('T')[0],
      });
      setTimeout(() => {
        setSuccess(false);
        onSuccess?.();
      }, 2000);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to post receipt');
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {success && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex gap-2">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-green-800">Receipt posted successfully</div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Debtor ID *</label>
          <Input
            name="debtor_id"
            type="number"
            value={formData.debtor_id}
            onChange={handleChange}
            placeholder="Enter debtor ID"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Receipt Date *</label>
          <Input
            name="transaction_date"
            type="date"
            value={formData.transaction_date}
            onChange={handleChange}
            required
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Receipt Amount *</label>
          <Input
            name="amount"
            type="number"
            step="0.01"
            value={formData.amount}
            onChange={handleChange}
            placeholder="0.00"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Cheque/Reference #</label>
          <Input
            name="reference_number"
            value={formData.reference_number}
            onChange={handleChange}
            placeholder="Cheque or reference number"
          />
        </div>
      </div>

      <Button
        type="submit"
        disabled={mutation.isPending || !formData.debtor_id || !formData.amount}
        className="bg-green-600 hover:bg-green-700 w-full"
      >
        {mutation.isPending && <Loader className="w-4 h-4 mr-2 animate-spin" />}
        Post Receipt
      </Button>
    </form>
  );
}

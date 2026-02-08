'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, AlertCircle, CheckCircle } from 'lucide-react';
import type { TransactionType } from '@/lib/types/debtors';

interface TransactionFormProps {
  onSuccess?: () => void;
}

export default function TransactionForm({ onSuccess }: TransactionFormProps) {
  const [formData, setFormData] = useState({
    debtor_id: '',
    amount: '',
    description: '',
    transaction_date: new Date().toISOString().split('T')[0],
    transaction_type: 'IN' as TransactionType,
  });

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!formData.debtor_id || !formData.amount) throw new Error('Missing required fields');

      switch (formData.transaction_type) {
        case 'JD':
          return debtorsApi.transactions.postDebit({
            debtor_id: parseInt(formData.debtor_id),
            amount: parseFloat(formData.amount),
            description: formData.description,
            transaction_date: formData.transaction_date,
          });
        case 'JC':
          return debtorsApi.transactions.postCredit({
            debtor_id: parseInt(formData.debtor_id),
            amount: parseFloat(formData.amount),
            description: formData.description,
            transaction_date: formData.transaction_date,
          });
        default:
          return debtorsApi.transactions.create({
            debtor_id: parseInt(formData.debtor_id),
            amount: parseFloat(formData.amount),
            description: formData.description,
            transaction_date: formData.transaction_date,
            transaction_type: formData.transaction_type,
          });
      }
    },
    onSuccess: () => {
      setSuccess(true);
      setFormData({
        debtor_id: '',
        amount: '',
        description: '',
        transaction_date: new Date().toISOString().split('T')[0],
        transaction_type: 'IN' as TransactionType,
      });
      setTimeout(() => {
        setSuccess(false);
        onSuccess?.();
      }, 2000);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to post transaction');
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
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
          <div className="text-sm text-green-800">Transaction posted successfully</div>
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
          <label className="block text-sm font-medium mb-1">Transaction Date *</label>
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
          <label className="block text-sm font-medium mb-1">Transaction Type *</label>
          <select
            name="transaction_type"
            value={formData.transaction_type}
            onChange={handleChange}
            className="w-full border rounded-md px-3 py-2"
          >
            <option value="IN">Invoice</option>
            <option value="CN">Credit Note</option>
            <option value="JD">Journal Debit</option>
            <option value="JC">Journal Credit</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Amount *</label>
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
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Description</label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          placeholder="Transaction details..."
          className="w-full border rounded-md px-3 py-2 text-sm"
          rows={3}
        />
      </div>

      <Button
        type="submit"
        disabled={mutation.isPending || !formData.debtor_id || !formData.amount}
        className="bg-blue-600 hover:bg-blue-700 w-full"
      >
        {mutation.isPending && <Loader className="w-4 h-4 mr-2 animate-spin" />}
        Post Transaction
      </Button>
    </form>
  );
}

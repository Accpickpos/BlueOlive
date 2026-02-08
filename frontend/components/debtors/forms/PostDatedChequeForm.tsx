'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, AlertCircle, CheckCircle } from 'lucide-react';

interface PostDatedChequeFormProps {
  onSuccess?: () => void;
}

export default function PostDatedChequeForm({ onSuccess }: PostDatedChequeFormProps) {
  const [formData, setFormData] = useState({
    debtor_id: '',
    cheque_number: '',
    amount: '',
    expected_date: '',
    bank: '',
    notes: '',
  });

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!formData.debtor_id || !formData.cheque_number || !formData.amount || !formData.expected_date) {
        throw new Error('All required fields must be filled');
      }
      return debtorsApi.pdcs.create({
        debtor_id: parseInt(formData.debtor_id),
        cheque_number: formData.cheque_number,
        amount: parseFloat(formData.amount),
        expected_date: formData.expected_date,
        bank: formData.bank || undefined,
        status: 'OUTSTANDING',
        notes: formData.notes || undefined,
      });
    },
    onSuccess: () => {
      setSuccess(true);
      setFormData({
        debtor_id: '',
        cheque_number: '',
        amount: '',
        expected_date: '',
        bank: '',
        notes: '',
      });
      setTimeout(() => {
        setSuccess(false);
        onSuccess?.();
      }, 2000);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to record PDC');
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
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
          <div className="text-sm text-green-800">PDC recorded successfully</div>
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
          <label className="block text-sm font-medium mb-1">Cheque Number *</label>
          <Input
            name="cheque_number"
            value={formData.cheque_number}
            onChange={handleChange}
            placeholder="Cheque #"
            required
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
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
        <div>
          <label className="block text-sm font-medium mb-1">Expected Date *</label>
          <Input
            name="expected_date"
            type="date"
            value={formData.expected_date}
            onChange={handleChange}
            required
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Bank</label>
        <Input
          name="bank"
          value={formData.bank}
          onChange={handleChange}
          placeholder="Bank name"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Notes</label>
        <textarea
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          placeholder="Any additional notes..."
          className="w-full border rounded-md px-3 py-2 text-sm"
          rows={2}
        />
      </div>

      <Button
        type="submit"
        disabled={mutation.isPending || !formData.debtor_id || !formData.cheque_number || !formData.amount || !formData.expected_date}
        className="bg-blue-600 hover:bg-blue-700 w-full"
      >
        {mutation.isPending && <Loader className="w-4 h-4 mr-2 animate-spin" />}
        Record PDC
      </Button>
    </form>
  );
}

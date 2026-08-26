'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { getApiErrorMessage } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowLeft, AlertCircle, CheckCircle } from 'lucide-react';

const TRANSACTION_TYPES: Array<{ value: string; label: string }> = [
  { value: 'CASH_SALE', label: 'Cash Sale' },
  { value: 'INVOICE', label: 'Invoice' },
  { value: 'RECEIPT', label: 'Receipt on Account' },
  { value: 'CREDIT_NOTE', label: 'Credit Note' },
  { value: 'LAYBYE', label: 'Laybye' },
  { value: 'QUOTATION', label: 'Quotation' },
  { value: 'JOB_CARD', label: 'Job Card' },
  { value: 'REPAIR', label: 'Repair' },
  { value: 'PAYOUT', label: 'Payout' },
];

export default function CreateTransactionQueryPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    query_date: new Date().toISOString().split('T')[0],
    transaction_type: 'CASH_SALE',
    transaction_number: '',
    customer_name: '',
    contact_number: '',
    query_description: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (!formData.transaction_number.trim()) {
        throw new Error('Transaction number is required');
      }
      if (!formData.query_description.trim()) {
        throw new Error('Query description is required');
      }

      const queryNumber = `TQ-${Date.now()}`;

      await posAPI.createTransactionQuery({
        query_number: queryNumber,
        query_date: formData.query_date,
        transaction_type: formData.transaction_type as any,
        transaction_number: formData.transaction_number,
        customer_name: formData.customer_name || undefined,
        contact_number: formData.contact_number || undefined,
        query_description: formData.query_description,
      });

      setSuccess('Query logged successfully');
      setTimeout(() => router.push('/dashboard/pos/transaction-query'), 2000);
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to log query'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="text-blue-600 hover:text-blue-700"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Log Transaction Query</h1>
          <p className="text-sm text-gray-500">Record a customer query about a past transaction</p>
        </div>
      </div>

      <div className="p-6">
        {error && (
          <Card className="border-red-200 bg-red-50 mb-6">
            <CardContent className="pt-6 flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <p className="text-red-800">{error}</p>
            </CardContent>
          </Card>
        )}

        {success && (
          <Card className="border-green-200 bg-green-50 mb-6">
            <CardContent className="pt-6 flex gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
              <p className="text-green-800">{success}</p>
            </CardContent>
          </Card>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Query Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Query Date *
                  </label>
                  <Input
                    type="date"
                    name="query_date"
                    value={formData.query_date}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Transaction Type *
                  </label>
                  <select
                    name="transaction_type"
                    value={formData.transaction_type}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg bg-white"
                  >
                    {TRANSACTION_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Transaction Number *
                </label>
                <Input
                  type="text"
                  name="transaction_number"
                  placeholder="e.g. the cash sale or invoice number being queried"
                  value={formData.transaction_number}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Customer Name
                  </label>
                  <Input
                    type="text"
                    name="customer_name"
                    placeholder="Optional"
                    value={formData.customer_name}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contact Number
                  </label>
                  <Input
                    type="text"
                    name="contact_number"
                    placeholder="Optional"
                    value={formData.contact_number}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Query Description *
                </label>
                <textarea
                  name="query_description"
                  placeholder="What is the customer asking about or disputing?"
                  value={formData.query_description}
                  onChange={handleChange}
                  rows={4}
                  className="w-full px-3 py-2 border rounded-lg"
                  required
                />
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-4 justify-end">
            <Button
              type="button"
              onClick={() => router.back()}
              variant="outline"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Log Query'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

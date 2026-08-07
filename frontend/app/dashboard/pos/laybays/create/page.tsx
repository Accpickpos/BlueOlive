'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowLeft, AlertCircle, CheckCircle } from 'lucide-react';

export default function CreateLaybyePage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    laybye_number: '',
    customer_name: '',
    telephone: '',
    total_amount: '',
    deposit_amount: '',
    laybye_date: new Date().toISOString().split('T')[0],
    expiry_date: '',
    item_description: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const outstandingBalance =
    parseFloat(String(formData.total_amount) || '0') - parseFloat(String(formData.deposit_amount) || '0');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (!formData.customer_name.trim()) {
        throw new Error('Customer name is required');
      }
      if (!formData.total_amount || parseFloat(formData.total_amount) <= 0) {
        throw new Error('Total amount must be greater than 0');
      }
      if (!formData.expiry_date) {
        throw new Error('Expiry date is required');
      }

      const laybyeNumber = formData.laybye_number.trim() || `LAY-${Date.now()}`;

      await posAPI.createLaybye({
        laybye_number: laybyeNumber,
        customer_name: formData.customer_name,
        telephone: formData.telephone,
        laybye_date: formData.laybye_date,
        expiry_date: formData.expiry_date,
        total_amount: parseFloat(formData.total_amount),
        deposit_amount: parseFloat(String(formData.deposit_amount)) || 0,
        comment1: formData.item_description.slice(0, 30),
      });

      setSuccess('Laybye record created successfully');
      setTimeout(() => router.push('/dashboard/pos/laybays'), 2000);
    } catch (err: any) {
      setError(err?.response?.data?.error || (err instanceof Error ? err.message : 'Failed to create laybye'));
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
          <h1 className="text-2xl font-bold text-gray-900">Create Laybye</h1>
          <p className="text-sm text-gray-500">Record new laybye arrangement</p>
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
          {/* Laybye Details */}
          <Card>
            <CardHeader>
              <CardTitle>Laybye Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Laybye Number
                  </label>
                  <Input
                    type="text"
                    name="laybye_number"
                    placeholder="Auto-generated if left blank"
                    value={formData.laybye_number}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Customer Name *
                  </label>
                  <Input
                    type="text"
                    name="customer_name"
                    placeholder="Customer name"
                    value={formData.customer_name}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Telephone
                </label>
                <Input
                  type="text"
                  name="telephone"
                  placeholder="Customer telephone"
                  value={formData.telephone}
                  onChange={handleChange}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Item Description
                </label>
                <textarea
                  name="item_description"
                  placeholder="What is on laybye? (max 30 characters — there's no line-item support yet)"
                  value={formData.item_description}
                  onChange={handleChange}
                  rows={2}
                  maxLength={30}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Total Amount *
                  </label>
                  <Input
                    type="number"
                    name="total_amount"
                    placeholder="0.00"
                    step="0.01"
                    value={formData.total_amount || ''}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Deposit *
                  </label>
                  <Input
                    type="number"
                    name="deposit_amount"
                    placeholder="0.00"
                    step="0.01"
                    value={formData.deposit_amount || ''}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Outstanding
                  </label>
                  <div className="px-3 py-2 border rounded-lg bg-gray-50">
                    <p className="font-bold text-blue-900">R{outstandingBalance.toFixed(2)}</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Laybye Date
                  </label>
                  <Input
                    type="date"
                    name="laybye_date"
                    value={formData.laybye_date}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Expiry Date *
                  </label>
                  <Input
                    type="date"
                    name="expiry_date"
                    value={formData.expiry_date}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
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
              {loading ? 'Saving...' : 'Create Laybye'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

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

export default function CreateRepairPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    customer_name: '',
    telephone: '',
    address_line1: '',
    order_number: '',
    customer_reference: '',
    date_required: '',
    quoted_value: '',
    repair_details: '',
    comment1: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (!formData.customer_name.trim()) {
        throw new Error('Customer name is required');
      }
      if (!formData.date_required) {
        throw new Error('Date required is required');
      }
      if (!formData.repair_details.trim()) {
        throw new Error('Repair details are required');
      }

      const repairNumber = `REP-${Date.now()}`;

      await posAPI.createRepairControl({
        repair_number: repairNumber,
        customer_name: formData.customer_name,
        telephone: formData.telephone || undefined,
        address_line1: formData.address_line1 || undefined,
        order_number: formData.order_number || undefined,
        customer_reference: formData.customer_reference || undefined,
        date_required: formData.date_required,
        quoted_value: formData.quoted_value ? parseFloat(formData.quoted_value) : undefined,
        repair_details: formData.repair_details,
        comment1: formData.comment1 || undefined,
      });

      setSuccess('Repair voucher created successfully');
      setTimeout(() => router.push('/dashboard/pos/repair-controls'), 2000);
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to create repair voucher'));
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
          <h1 className="text-2xl font-bold text-gray-900">Create Repair Job</h1>
          <p className="text-sm text-gray-500">Record new item for repair</p>
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
          {/* Customer & Item Details */}
          <Card>
            <CardHeader>
              <CardTitle>Repair Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Telephone
                  </label>
                  <Input
                    type="text"
                    name="telephone"
                    placeholder="Optional"
                    value={formData.telephone}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Address
                </label>
                <Input
                  type="text"
                  name="address_line1"
                  placeholder="Optional"
                  value={formData.address_line1}
                  onChange={handleChange}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Order Number
                  </label>
                  <Input
                    type="text"
                    name="order_number"
                    placeholder="Optional"
                    value={formData.order_number}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Customer Reference
                  </label>
                  <Input
                    type="text"
                    name="customer_reference"
                    placeholder="Optional"
                    value={formData.customer_reference}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Repair Details *
                </label>
                <textarea
                  name="repair_details"
                  placeholder="Description of goods, serial number, fault description"
                  value={formData.repair_details}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-3 py-2 border rounded-lg"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date Required *
                  </label>
                  <Input
                    type="date"
                    name="date_required"
                    value={formData.date_required}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Quoted Value (excl. VAT)
                  </label>
                  <Input
                    type="number"
                    name="quoted_value"
                    placeholder="0.00"
                    step="0.01"
                    value={formData.quoted_value || ''}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Comments
                </label>
                <textarea
                  name="comment1"
                  placeholder="Additional comments"
                  value={formData.comment1}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-lg"
                />
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
              {loading ? 'Saving...' : 'Create Repair Job'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

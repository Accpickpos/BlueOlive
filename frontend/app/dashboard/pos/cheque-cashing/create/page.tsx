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

export default function CreateChequeCashingPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    transaction_date: new Date().toISOString().split('T')[0],
    drawer_name: '',
    id_number: '',
    telephone: '',
    cheque_number: '',
    bank_name: '',
    branch_code: '',
    account_number: '',
    cheque_amount: '',
    commission: '',
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
      if (!formData.cheque_number.trim()) {
        throw new Error('Cheque number is required');
      }
      if (!formData.drawer_name.trim()) {
        throw new Error("Drawer's name is required");
      }
      if (!formData.id_number.trim()) {
        throw new Error("Drawer's ID number is required");
      }
      if (!formData.bank_name.trim()) {
        throw new Error('Bank name is required');
      }
      if (!formData.cheque_amount || parseFloat(formData.cheque_amount) <= 0) {
        throw new Error('Cheque amount must be greater than 0');
      }
      if (!user?.id) {
        throw new Error('Could not determine the logged-in cashier');
      }

      const transactionNumber = `CHQ-${Date.now()}`;

      await posAPI.createCashACheque({
        transaction_number: transactionNumber,
        transaction_date: formData.transaction_date,
        drawer_name: formData.drawer_name,
        id_number: formData.id_number,
        telephone: formData.telephone || undefined,
        cheque_number: formData.cheque_number,
        bank_name: formData.bank_name,
        branch_code: formData.branch_code || undefined,
        account_number: formData.account_number || undefined,
        cheque_amount: parseFloat(formData.cheque_amount),
        commission: formData.commission ? parseFloat(formData.commission) : undefined,
        cashier: Number(user.id),
      });

      setSuccess('Cheque cashing recorded successfully');
      setTimeout(() => router.push('/dashboard/pos/cheque-cashing'), 2000);
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to create cheque cashing record'));
    } finally {
      setLoading(false);
    }
  };

  const chequeAmount = parseFloat(formData.cheque_amount) || 0;
  const commission = parseFloat(formData.commission) || 0;
  const cashToPay = chequeAmount - commission;

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
          <h1 className="text-2xl font-bold text-gray-900">Cash Cheque</h1>
          <p className="text-sm text-gray-500">Record cheque cashing with bank details</p>
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
          {/* Cheque Details */}
          <Card>
            <CardHeader>
              <CardTitle>Cheque Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Transaction Date *
                  </label>
                  <Input
                    type="date"
                    name="transaction_date"
                    value={formData.transaction_date}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cheque Amount *
                  </label>
                  <Input
                    type="number"
                    name="cheque_amount"
                    placeholder="0.00"
                    step="0.01"
                    value={formData.cheque_amount || ''}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Drawer's Name *
                  </label>
                  <Input
                    type="text"
                    name="drawer_name"
                    placeholder="Person who wrote the cheque"
                    value={formData.drawer_name}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ID Number *
                  </label>
                  <Input
                    type="text"
                    name="id_number"
                    placeholder="Drawer's ID number"
                    value={formData.id_number}
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
                  placeholder="Optional"
                  value={formData.telephone}
                  onChange={handleChange}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cheque Number *
                  </label>
                  <Input
                    type="text"
                    name="cheque_number"
                    placeholder="CHQ-12345"
                    value={formData.cheque_number}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bank Name *
                  </label>
                  <Input
                    type="text"
                    name="bank_name"
                    placeholder="Bank name"
                    value={formData.bank_name}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Branch Code
                  </label>
                  <Input
                    type="text"
                    name="branch_code"
                    placeholder="Optional"
                    value={formData.branch_code}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Account Number
                  </label>
                  <Input
                    type="text"
                    name="account_number"
                    placeholder="Optional"
                    value={formData.account_number}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Commission
                </label>
                <Input
                  type="number"
                  name="commission"
                  placeholder="0.00"
                  step="0.01"
                  value={formData.commission || ''}
                  onChange={handleChange}
                />
              </div>

              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <p className="text-sm text-gray-600 mb-1">Cash to Pay Out</p>
                <p className="text-2xl font-bold text-blue-900">R{cashToPay.toFixed(2)}</p>
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
              {loading ? 'Saving...' : 'Record Cheque Cashing'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

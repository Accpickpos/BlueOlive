'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Loader, AlertCircle, CheckCircle } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { DebtorAccount, DebtorCreateData, DebtorEditData } from '@/lib/types/debtors';

interface DebtorAccountFormProps {
  initialData?: DebtorAccount;
  isEdit?: boolean;
  onSuccess?: () => void;
}

export default function DebtorAccountForm({
  initialData,
  isEdit = false,
  onSuccess,
}: DebtorAccountFormProps) {
  const [formData, setFormData] = useState<any>(
    initialData || {
      acctype: 'BF',
      is_active: true,
      price: 1,
    }
  );

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      if (isEdit && initialData?.id) {
        return debtorsApi.accounts.update(initialData.id, formData as DebtorEditData);
      } else {
        return debtorsApi.accounts.create(formData as DebtorCreateData);
      }
    },
    onSuccess: () => {
      setSuccess(true);
      setTimeout(() => {
        onSuccess?.();
      }, 1500);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to save account');
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev: any) => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.dname?.trim()) {
      setError('Debtor name is required');
      return;
    }
    mutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {success && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex gap-2">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-green-800">
            {isEdit ? 'Account updated successfully' : 'Account created successfully'}
          </div>
        </div>
      )}

      <Tabs defaultValue="info" className="w-full">
        <TabsList className="grid w-full grid-cols-5 mb-6">
          <TabsTrigger value="info">Info</TabsTrigger>
          <TabsTrigger value="addresses">Addresses</TabsTrigger>
          <TabsTrigger value="pricing">Pricing</TabsTrigger>
          <TabsTrigger value="credit">Credit</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Info Tab */}
        <TabsContent value="info" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Account Number</label>
              <Input
                name="dno"
                value={formData.dno || ''}
                onChange={handleChange}
                placeholder="Auto-generated"
                disabled={isEdit}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-red-600">* Debtor Name</label>
              <Input
                name="dname"
                value={formData.dname || ''}
                onChange={handleChange}
                placeholder="Company name"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Short Name</label>
              <Input
                name="dsname"
                value={formData.dsname || ''}
                onChange={handleChange}
                placeholder="Max 20 chars"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Contact Person</label>
              <Input
                name="dcontact"
                value={formData.dcontact || ''}
                onChange={handleChange}
                placeholder="Name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Account Type</label>
              <select
                name="acctype"
                value={formData.acctype || 'BF'}
                onChange={handleChange}
                className="w-full border rounded-md px-3 py-2"
              >
                <option value="BF">Balance Forward</option>
                <option value="OI">Open Item</option>
                <option value="CS">Cash Sale</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <Input
                name="email"
                type="email"
                value={formData.email || ''}
                onChange={handleChange}
                placeholder="email@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Telephone 1</label>
              <Input
                name="dtel"
                value={formData.dtel || ''}
                onChange={handleChange}
                placeholder="Primary phone"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Fax</label>
              <Input
                name="dfax"
                value={formData.dfax || ''}
                onChange={handleChange}
                placeholder="Fax number"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Tax/VAT Number</label>
            <Input
              name="dtaxno"
              value={formData.dtaxno || ''}
              onChange={handleChange}
              placeholder="VAT registration"
            />
          </div>
        </TabsContent>

        {/* Addresses Tab */}
        <TabsContent value="addresses" className="space-y-6">
          <div>
            <h3 className="text-sm font-bold mb-3 text-gray-700">Postal Address</h3>
            <div className="space-y-2">
              <Input
                name="dadd1"
                value={formData.dadd1 || ''}
                onChange={handleChange}
                placeholder="Line 1"
              />
              <Input
                name="dadd2"
                value={formData.dadd2 || ''}
                onChange={handleChange}
                placeholder="Line 2"
              />
              <Input
                name="dadd3"
                value={formData.dadd3 || ''}
                onChange={handleChange}
                placeholder="Line 3 / City"
              />
            </div>
          </div>

          <div>
            <h3 className="text-sm font-bold mb-3 text-gray-700">Delivery Address</h3>
            <div className="space-y-2">
              <Input
                name="delad1"
                value={formData.delad1 || ''}
                onChange={handleChange}
                placeholder="Line 1"
              />
              <Input
                name="delad2"
                value={formData.delad2 || ''}
                onChange={handleChange}
                placeholder="Line 2"
              />
              <Input
                name="delad3"
                value={formData.delad3 || ''}
                onChange={handleChange}
                placeholder="Line 3"
              />
              <Input
                name="delad4"
                value={formData.delad4 || ''}
                onChange={handleChange}
                placeholder="Line 4 / City"
              />
            </div>
          </div>
        </TabsContent>

        {/* Pricing Tab */}
        <TabsContent value="pricing" className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Price List</label>
              <select
                name="price"
                value={formData.price || 1}
                onChange={handleChange}
                className="w-full border rounded-md px-3 py-2"
              >
                <option value={1}>List 1</option>
                <option value={2}>List 2</option>
                <option value={3}>List 3</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Trade Discount (%)</label>
              <Input
                name="ddiscper"
                type="number"
                step="0.01"
                value={formData.ddiscper || ''}
                onChange={handleChange}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Prompt Discount (%)</label>
              <Input
                name="pdisc"
                type="number"
                step="0.01"
                value={formData.pdisc || ''}
                onChange={handleChange}
                placeholder="0.00"
              />
            </div>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg text-sm text-blue-800">
            <p>Trade discount is applied automatically to all invoices for this customer.</p>
            <p className="mt-1">Prompt discount is earned for payment within terms.</p>
          </div>
        </TabsContent>

        {/* Credit Tab */}
        <TabsContent value="credit" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Credit Limit</label>
              <Input
                name="dclimit"
                type="number"
                step="0.01"
                value={formData.dclimit || ''}
                onChange={handleChange}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Credit Terms (days)</label>
              <Input
                name="credit_terms"
                type="number"
                value={formData?.credit_terms || ''}
                onChange={handleChange}
                placeholder="30"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="chargeInterest"
              name="dintflag"
              checked={formData.dintflag || false}
              onChange={handleChange}
              className="w-4 h-4"
            />
            <label htmlFor="chargeInterest" className="text-sm">
              Charge interest on overdue balances
            </label>
          </div>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="isActive"
                name="is_active"
                checked={formData.is_active !== false}
                onChange={handleChange}
                className="w-4 h-4"
              />
              <label htmlFor="isActive" className="text-sm font-medium">
                Account is active
              </label>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="blocked"
                name="blockflag"
                checked={formData.blockflag || false}
                onChange={handleChange}
                className="w-4 h-4"
              />
              <label htmlFor="blocked" className="text-sm font-medium text-red-600">
                Block account (prevents new transactions)
              </label>
            </div>
          </div>

          {isEdit && formData.id && (
            <Card className="p-4 bg-gray-50">
              <p className="text-xs text-gray-600">
                <strong>Created:</strong> {formData.created_at && new Date(formData.created_at).toLocaleString()}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                <strong>Updated:</strong> {formData.updated_at && new Date(formData.updated_at).toLocaleString()}
              </p>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Submit Buttons */}
      <div className="flex gap-3 pt-6 border-t">
        <Button
          type="submit"
          disabled={mutation.isPending}
          className="bg-blue-600 hover:bg-blue-700"
        >
          {mutation.isPending && <Loader className="w-4 h-4 mr-2 animate-spin" />}
          {isEdit ? 'Update Account' : 'Create Account'}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => window.history.back()}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}

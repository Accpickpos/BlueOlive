'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import type { CreditorAccount, CreditorCreateData } from '@/lib/types/creditors';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader } from 'lucide-react';

export default function CreditorAccountFormPage() {
  const router = useRouter();
  const params = useParams();
  const accountId = params.id as string;
  const isNew = accountId === 'new';

  const [formData, setFormData] = useState<Partial<CreditorAccount>>({
    account_category: 'B',
    credit_terms: 30,
    payment_terms_days: 30,
    prompt_payment_discount_percent: 0,
    update_selling_price_on_receipt: false,
  });

  const { data: account, isLoading } = useQuery({
    queryKey: ['creditor-account', accountId],
    queryFn: () => creditorsApi.accounts.get(accountId),
    enabled: !isNew,
  });

  const mutations = useMutation({
    mutationFn: (data: Partial<CreditorAccount>) => {
      const createData: CreditorCreateData = {
        supplier_number: data.supplier_number || '',
        name: data.name || '',
        contact_person: data.contact_person,
        telephone: data.telephone,
        fax: data.fax,
        email: data.email,
        physical_address_line1: data.physical_address_line1,
        physical_address_line2: data.physical_address_line2,
        physical_address_line3: data.physical_address_line3,
        postal_address_line1: data.postal_address_line1,
        postal_address_line2: data.postal_address_line2,
        postal_address_line3: data.postal_address_line3,
        our_account_number: data.our_account_number,
        credit_terms: data.credit_terms,
        payment_terms_days: data.payment_terms_days,
        account_category: data.account_category,
        sales_area: data.sales_area,
        update_selling_price_on_receipt: data.update_selling_price_on_receipt,
        prompt_payment_discount_percent: data.prompt_payment_discount_percent,
        bank_name: data.bank_name,
        branch_code: data.branch_code,
        account_number: data.account_number,
        is_active: data.is_active,
      };
      return isNew ? creditorsApi.accounts.create(createData) : creditorsApi.accounts.update(accountId, data);
    },
    onSuccess: () => {
      router.push('/dashboard/admin/creditors/maintenance/accounts');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutations.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (account && !isNew) {
    Object.assign(formData, account);
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">{isNew ? 'New Creditor Account' : 'Edit Creditor Account'}</h1>
        <p className="text-gray-600 mt-1">
          {isNew ? 'Create a new supplier account' : `Update account details for ${formData.name}`}
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit}>
        {/* Account Details */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Account Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Account Number</label>
              <Input
                type="text"
                value={formData.supplier_number || ''}
                onChange={(e) => setFormData({ ...formData, supplier_number: e.target.value })}
                placeholder="Auto-allocated via Page Down"
                disabled={!isNew}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <Input
                type="text"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Account Type</label>
              <select
                value={formData.account_category || 'B'}
                onChange={(e) => setFormData({ ...formData, account_category: e.target.value as 'B' | 'O' | '' })}
                className="w-full border border-gray-300 rounded px-3 py-2"
              >
                <option value="B">Balance Brought Forward</option>
                <option value="O">Open Item</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Contact Person</label>
              <Input
                type="text"
                value={formData.contact_person || ''}
                onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
              />
            </div>
          </div>
        </Card>

        {/* Address Details */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Address Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Physical Address</label>
              <textarea
                value={formData.physical_address_line1 || ''}
                onChange={(e) => setFormData({ ...formData, physical_address_line1: e.target.value })}
                className="w-full border border-gray-300 rounded px-3 py-2"
                rows={3}
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Postal Address</label>
              <textarea
                value={formData.postal_address_line1 || ''}
                onChange={(e) => setFormData({ ...formData, postal_address_line1: e.target.value })}
                className="w-full border border-gray-300 rounded px-3 py-2"
                rows={3}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Telephone</label>
              <Input
                type="tel"
                value={formData.telephone || ''}
                onChange={(e) => setFormData({ ...formData, telephone: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Fax</label>
              <Input
                type="tel"
                value={formData.fax || ''}
                onChange={(e) => setFormData({ ...formData, fax: e.target.value })}
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Email</label>
              <Input
                type="email"
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
          </div>
        </Card>

        {/* Trade Details */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Trade Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Our Account Number</label>
              <Input
                type="text"
                value={formData.our_account_number || ''}
                onChange={(e) => setFormData({ ...formData, our_account_number: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Credit Terms (Days)</label>
              <Input
                type="number"
                value={formData.credit_terms || 30}
                onChange={(e) => setFormData({ ...formData, credit_terms: parseInt(e.target.value) })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Payment Discount %</label>
              <Input
                type="number"
                step="0.01"
                value={formData.prompt_payment_discount_percent || 0}
                onChange={(e) => setFormData({ ...formData, prompt_payment_discount_percent: parseFloat(e.target.value) })}
              />
            </div>
          </div>
        </Card>

        {/* Banking Details */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Banking Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Bank Name</label>
              <Input
                type="text"
                value={formData.bank_name || ''}
                onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Branch Code</label>
              <Input
                type="text"
                value={formData.branch_code || ''}
                onChange={(e) => setFormData({ ...formData, branch_code: e.target.value })}
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Account Number</label>
              <Input
                type="text"
                value={formData.account_number || ''}
                onChange={(e) => setFormData({ ...formData, account_number: e.target.value })}
              />
            </div>
          </div>
        </Card>

        {/* Options */}
        <Card className="p-6 mb-6">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="update_price"
              checked={formData.update_selling_price_on_receipt || false}
              onChange={(e) => setFormData({ ...formData, update_selling_price_on_receipt: e.target.checked })}
              className="w-4 h-4"
            />
            <label htmlFor="update_price" className="text-sm font-medium">
              Update Selling Price on Stock Receipts
            </label>
          </div>
        </Card>

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700"
            disabled={mutations.isPending}
          >
            {mutations.isPending ? 'Saving...' : 'Save Account'}
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

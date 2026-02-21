'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import settingsApi from '@/lib/settingsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader } from 'lucide-react';

export default function ExpenseInvoiceForm() {
  const router = useRouter();
  const params = useParams();
  const invoiceId = params.id as string;
  const isNew = invoiceId === 'new';

  const [formData, setFormData] = useState({
    supplier_id: 0,
    invoice_number: '',
    invoice_date: new Date().toISOString().split('T')[0],
    due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    category_id: 0,
    description: '',
    amount: 0,
    vat_rate: 14,
    vat_option: 'I',
  });

  const { data: suppliers } = useQuery({
    queryKey: ['creditors-accounts'],
    queryFn: () => creditorsApi.accounts.list({ page_size: 500 }),
  });

  const { data: categories } = useQuery({
    queryKey: ['expense-categories'],
    queryFn: () => settingsApi.expenseCategories.list({ page_size: 100 }),
  });

  const { data: invoiceData, isLoading } = useQuery({
    queryKey: ['expense-invoice', invoiceId],
    queryFn: () => creditorsApi.invoices.get(invoiceId),
    enabled: !isNew,
  });

  const mutation = useMutation({
    mutationFn: (data: any) =>
      isNew
        ? creditorsApi.invoices.create({ ...data, transaction_type: 'INVOICE_EXPENSE' })
        : creditorsApi.invoices.update(invoiceId, data),
    onSuccess: () => {
      router.push('/dashboard/admin/creditors/transactions/invoices/expense');
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

  const taxableAmount = formData.vat_option === 'I' 
    ? formData.amount / (1 + formData.vat_rate / 100)
    : formData.amount;
  const taxAmount = taxableAmount * (formData.vat_rate / 100);
  const finalAmount = formData.vat_option === 'I' ? formData.amount : taxableAmount + taxAmount;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">{isNew ? 'New Expense Invoice' : 'Edit Expense Invoice'}</h1>
        <p className="text-gray-600 mt-1">Record an expense invoice from a supplier</p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Invoice Details */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Invoice Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Supplier</label>
              <select
                value={formData.supplier_id}
                onChange={(e) => setFormData({ ...formData, supplier_id: parseInt(e.target.value) })}
                className="w-full border border-gray-300 rounded px-3 py-2"
                required
              >
                <option value={0}>Select Supplier...</option>
                {suppliers?.results?.map((supplier: any) => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.account_number} - {supplier.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Invoice Number</label>
              <Input
                type="text"
                value={formData.invoice_number}
                onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Invoice Date</label>
              <Input
                type="date"
                value={formData.invoice_date}
                onChange={(e) => setFormData({ ...formData, invoice_date: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Due Date</label>
              <Input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Expense Category</label>
              <select
                value={formData.category_id}
                onChange={(e) => setFormData({ ...formData, category_id: parseInt(e.target.value) })}
                className="w-full border border-gray-300 rounded px-3 py-2"
                required
              >
                <option value={0}>Select Category...</option>
                {categories?.results?.map((category: any) => (
                  <option key={category.id} value={category.id}>
                    {category.category_number} - {category.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </Card>

        {/* Amount Details */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Amount Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Description/Particulars</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full border border-gray-300 rounded px-3 py-2"
                rows={3}
                placeholder="Description of the expense"
                required
              />
            </div>
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
            <div>
              <label className="block text-sm font-medium mb-1">VAT Option</label>
              <select
                value={formData.vat_option}
                onChange={(e) => setFormData({ ...formData, vat_option: e.target.value })}
                className="w-full border border-gray-300 rounded px-3 py-2"
              >
                <option value="I">Inclusive (I)</option>
                <option value="E">Exclusive (E)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">VAT Rate (%)</label>
              <Input
                type="number"
                step="0.01"
                value={formData.vat_rate}
                onChange={(e) => setFormData({ ...formData, vat_rate: parseFloat(e.target.value) })}
              />
            </div>
          </div>
        </Card>

        {/* Totals */}
        <Card className="p-6 mb-6 bg-gray-50">
          <h3 className="font-bold mb-3">Amount Breakdown</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Taxable Amount:</span>
              <span className="font-bold">R {taxableAmount.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between">
              <span>VAT ({formData.vat_rate}%):</span>
              <span className="font-bold">R {taxAmount.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}</span>
            </div>
            <div className="border-t pt-2 flex justify-between">
              <span className="font-bold">Total Invoice:</span>
              <span className="font-bold text-lg text-blue-600">
                R {finalAmount.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </Card>

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700"
            disabled={mutation.isPending}
          >
            {mutation.isPending ? 'Saving...' : 'Save Invoice'}
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

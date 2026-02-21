'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, Trash2, Plus } from 'lucide-react';

interface GRNLineItem {
  id?: number;
  stock_code: string;
  description: string;
  quantity: number;
  unit_cost: number;
  tax_rate: number;
}

interface GRNData {
  supplier_id: number;
  invoice_number: string;
  invoice_date: string;
  vat_option: 'I' | 'E';
  line_items: GRNLineItem[];
  surcharge: number;
}

export default function StockReceiptForm() {
  const router = useRouter();
  const params = useParams();
  const grnId = params.id as string;
  const isNew = grnId === 'new';

  const [formData, setFormData] = useState<GRNData>({
    supplier_id: 0,
    invoice_number: '',
    invoice_date: new Date().toISOString().split('T')[0],
    vat_option: 'I',
    line_items: [{ stock_code: '', description: '', quantity: 0, unit_cost: 0, tax_rate: 14 }],
    surcharge: 0,
  });

  const { data: suppliers } = useQuery({
    queryKey: ['creditors-accounts'],
    queryFn: () => creditorsApi.accounts.list({ page_size: 500 }),
  });

  const { data: grn, isLoading } = useQuery({
    queryKey: ['grn', grnId],
    queryFn: () => creditorsApi.grns.get(grnId),
    enabled: !isNew,
  });

  const mutation = useMutation({
    mutationFn: (data: GRNData) => {
      const apiData: any = {
        creditor: data.supplier_id,
        transaction_date: data.invoice_date,
        supplier_invoice_number: data.invoice_number,
        inclusive_exclusive: data.vat_option === 'I' ? 'INC' as const : 'EXC' as const,
        surcharge_amount: data.surcharge,
        line_items: data.line_items.map((item) => ({
          stock_item: 0,
          quantity_received: item.quantity,
          unit_cost: item.unit_cost,
          tax_code: item.tax_rate,
        })),
      };
      return isNew 
        ? creditorsApi.grns.create(apiData) 
        : creditorsApi.grns.update(grnId, apiData);
    },
    onSuccess: () => {
      router.push('/dashboard/admin/creditors/transactions/stock-receipts');
    },
  });

  const calculateLineTotal = (item: GRNLineItem) => {
    const subtotal = item.quantity * item.unit_cost;
    if (formData.vat_option === 'I') {
      return subtotal;
    } else {
      return subtotal * (1 + item.tax_rate / 100);
    }
  };

  const calculateGrandTotal = () => {
    const itemsTotal = formData.line_items.reduce((sum, item) => sum + calculateLineTotal(item), 0);
    return itemsTotal + formData.surcharge;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  const addLineItem = () => {
    setFormData({
      ...formData,
      line_items: [...formData.line_items, { stock_code: '', description: '', quantity: 0, unit_cost: 0, tax_rate: 14 }],
    });
  };

  const removeLineItem = (index: number) => {
    setFormData({
      ...formData,
      line_items: formData.line_items.filter((_, i) => i !== index),
    });
  };

  const updateLineItem = (index: number, updates: Partial<GRNLineItem>) => {
    const newItems = [...formData.line_items];
    newItems[index] = { ...newItems[index], ...updates };
    setFormData({ ...formData, line_items: newItems });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">{isNew ? 'New Stock Receipt' : 'Edit Stock Receipt'}</h1>
        <p className="text-gray-600 mt-1">Record goods received from a supplier</p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Header Section */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Receipt Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div>
              <label className="block text-sm font-medium mb-1">VAT Option</label>
              <select
                value={formData.vat_option}
                onChange={(e) => setFormData({ ...formData, vat_option: e.target.value as 'I' | 'E' })}
                className="w-full border border-gray-300 rounded px-3 py-2"
              >
                <option value="I">Inclusive (I)</option>
                <option value="E">Exclusive (E)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Surcharge (R)</label>
              <Input
                type="number"
                step="0.01"
                value={formData.surcharge}
                onChange={(e) => setFormData({ ...formData, surcharge: parseFloat(e.target.value) })}
              />
            </div>
          </div>
        </Card>

        {/* Line Items Section */}
        <Card className="p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">Line Items</h2>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addLineItem}
              className="flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Line
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left font-semibold">Stock Code</th>
                  <th className="px-2 py-2 text-left font-semibold">Description</th>
                  <th className="px-2 py-2 text-right font-semibold">Qty</th>
                  <th className="px-2 py-2 text-right font-semibold">Unit Cost</th>
                  <th className="px-2 py-2 text-right font-semibold">Tax %</th>
                  <th className="px-2 py-2 text-right font-semibold">Total</th>
                  <th className="px-2 py-2 text-center font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {formData.line_items.map((item, index) => (
                  <tr key={index} className="border-b">
                    <td className="px-2 py-2">
                      <Input
                        type="text"
                        value={item.stock_code}
                        onChange={(e) => updateLineItem(index, { stock_code: e.target.value })}
                        className="text-xs"
                        placeholder="e.g., SKU123"
                      />
                    </td>
                    <td className="px-2 py-2">
                      <Input
                        type="text"
                        value={item.description}
                        onChange={(e) => updateLineItem(index, { description: e.target.value })}
                        className="text-xs"
                        placeholder="Item description"
                      />
                    </td>
                    <td className="px-2 py-2">
                      <Input
                        type="number"
                        step="0.01"
                        value={item.quantity}
                        onChange={(e) => updateLineItem(index, { quantity: parseFloat(e.target.value) })}
                        className="text-xs text-right"
                      />
                    </td>
                    <td className="px-2 py-2">
                      <Input
                        type="number"
                        step="0.01"
                        value={item.unit_cost}
                        onChange={(e) => updateLineItem(index, { unit_cost: parseFloat(e.target.value) })}
                        className="text-xs text-right"
                      />
                    </td>
                    <td className="px-2 py-2">
                      <Input
                        type="number"
                        step="0.01"
                        value={item.tax_rate}
                        onChange={(e) => updateLineItem(index, { tax_rate: parseFloat(e.target.value) })}
                        className="text-xs text-right"
                      />
                    </td>
                    <td className="px-2 py-2 text-right font-bold text-xs">
                      R {calculateLineTotal(item).toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-2 py-2 text-center">
                      <Button
                        type="button"
                        variant="destructive"
                        size="sm"
                        className="w-8 h-8 p-0"
                        onClick={() => removeLineItem(index)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Totals */}
        <Card className="p-6 mb-6">
          <div className="flex justify-end">
            <div className="w-full md:w-72">
              <div className="flex justify-between mb-2">
                <span>Subtotal:</span>
                <span className="font-bold">
                  R {formData.line_items.reduce((sum, item) => sum + item.quantity * item.unit_cost, 0).toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between mb-2">
                <span>Surcharge:</span>
                <span className="font-bold">
                  R {formData.surcharge.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="border-t-2 pt-2 flex justify-between">
                <span className="font-bold">Total:</span>
                <span className="font-bold text-lg text-blue-600">
                  R {calculateGrandTotal().toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                </span>
              </div>
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
            {mutation.isPending ? 'Saving...' : 'Save Receipt'}
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

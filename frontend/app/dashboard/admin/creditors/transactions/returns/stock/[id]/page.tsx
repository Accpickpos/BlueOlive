'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader } from 'lucide-react';

export default function StockReturnForm() {
  const router = useRouter();
  const params = useParams();
  const returnId = params.id as string;
  const isNew = returnId === 'new';

  const [formData, setFormData] = useState({
    supplier_id: 0,
    return_date: new Date().toISOString().split('T')[0],
    return_reason: '',
    items: [
      {
        stock_code: '',
        description: '',
        quantity: 0,
        unit_value: 0,
      },
    ],
  });

  const { data: suppliers } = useQuery({
    queryKey: ['creditors-accounts'],
    queryFn: () => creditorsApi.accounts.list({ page_size: 500 }),
  });

  const { data: returnData, isLoading } = useQuery({
    queryKey: ['stock-return', returnId],
    queryFn: () => creditorsApi.creditNotes.get(returnId),
    enabled: !isNew,
  });

  const mutation = useMutation({
    mutationFn: (data: any) =>
      isNew
        ? creditorsApi.creditNotes.create({ ...data, transaction_type: 'RETURN_STOCK' })
        : creditorsApi.creditNotes.update(returnId, data),
    onSuccess: () => {
      router.push('/dashboard/admin/creditors/transactions/returns/stock');
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

  const totalValue = formData.items.reduce((sum, item) => sum + item.quantity * item.unit_value, 0);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">{isNew ? 'New Stock Return' : 'Edit Stock Return'}</h1>
        <p className="text-gray-600 mt-1">Record stock return to supplier</p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Return Details */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Return Details</h2>
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
              <label className="block text-sm font-medium mb-1">Return Date</label>
              <Input
                type="date"
                value={formData.return_date}
                onChange={(e) => setFormData({ ...formData, return_date: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Return Reason</label>
              <select
                value={formData.return_reason}
                onChange={(e) => setFormData({ ...formData, return_reason: e.target.value })}
                className="w-full border border-gray-300 rounded px-3 py-2"
                required
              >
                <option value="">Select Reason...</option>
                <option value="DEFECTIVE">Defective</option>
                <option value="WRONG_ITEM">Wrong Item</option>
                <option value="OVERSTOCK">Overstock</option>
                <option value="NO_LONGER_NEEDED">No Longer Needed</option>
                <option value="EXPIRED">Expired</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Items */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">Items Being Returned</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left font-semibold">Stock Code</th>
                  <th className="px-2 py-2 text-left font-semibold">Description</th>
                  <th className="px-2 py-2 text-right font-semibold">Qty Returned</th>
                  <th className="px-2 py-2 text-right font-semibold">Unit Value</th>
                  <th className="px-2 py-2 text-right font-semibold">Total</th>
                </tr>
              </thead>
              <tbody>
                {formData.items.map((item, index) => (
                  <tr key={index} className="border-b">
                    <td className="px-2 py-2">
                      <Input
                        type="text"
                        value={item.stock_code}
                        onChange={(e) => {
                          const newItems = [...formData.items];
                          newItems[index].stock_code = e.target.value;
                          setFormData({ ...formData, items: newItems });
                        }}
                        className="text-xs"
                        placeholder="Stock code"
                      />
                    </td>
                    <td className="px-2 py-2">
                      <Input
                        type="text"
                        value={item.description}
                        onChange={(e) => {
                          const newItems = [...formData.items];
                          newItems[index].description = e.target.value;
                          setFormData({ ...formData, items: newItems });
                        }}
                        className="text-xs"
                        placeholder="Description"
                      />
                    </td>
                    <td className="px-2 py-2">
                      <Input
                        type="number"
                        step="0.01"
                        value={item.quantity}
                        onChange={(e) => {
                          const newItems = [...formData.items];
                          newItems[index].quantity = parseFloat(e.target.value);
                          setFormData({ ...formData, items: newItems });
                        }}
                        className="text-xs text-right"
                      />
                    </td>
                    <td className="px-2 py-2">
                      <Input
                        type="number"
                        step="0.01"
                        value={item.unit_value}
                        onChange={(e) => {
                          const newItems = [...formData.items];
                          newItems[index].unit_value = parseFloat(e.target.value);
                          setFormData({ ...formData, items: newItems });
                        }}
                        className="text-xs text-right"
                      />
                    </td>
                    <td className="px-2 py-2 text-right font-bold">
                      R {(item.quantity * item.unit_value).toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Total */}
        <Card className="p-6 mb-6">
          <div className="flex justify-end w-full md:w-72">
            <div className="flex justify-between">
              <span className="font-bold">Total Return Value:</span>
              <span className="font-bold text-lg text-blue-600">
                R {totalValue.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
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
            {mutation.isPending ? 'Saving...' : 'Save Return'}
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

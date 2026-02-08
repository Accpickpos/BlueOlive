'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import { TransactionType } from '@/lib/types/creditors';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, Trash2, Plus } from 'lucide-react';

interface RFCItem {
  id?: number;
  stock_code: string;
  description: string;
  quantity: number;
  unit_value: number;
  return_reason: string;
}

interface RFCData {
  supplier_id: number;
  rfc_date: string;
  items: RFCItem[];
  status: 'pending' | 'approved' | 'credited' | 'replaced';
}

export default function RFCForm() {
  const router = useRouter();
  const params = useParams();
  const rfcId = params.id as string;
  const isNew = rfcId === 'new';
  const isEdit = params.id === 'edit';

  const [formData, setFormData] = useState<RFCData>({
    supplier_id: 0,
    rfc_date: new Date().toISOString().split('T')[0],
    items: [{ stock_code: '', description: '', quantity: 0, unit_value: 0, return_reason: '' }],
    status: 'pending',
  });

  const { data: suppliers } = useQuery({
    queryKey: ['creditors-accounts'],
    queryFn: () => creditorsApi.accounts.list({ page_size: 500 }),
  });

  const { data: rfc, isLoading } = useQuery({
    queryKey: ['rfc', rfcId],
    queryFn: () => creditorsApi.transactions.get(rfcId),
    enabled: !isNew && rfcId !== 'edit',
  });

  const mutation = useMutation({
    mutationFn: (data: RFCData) =>
      isNew ? creditorsApi.transactions.create({ ...data, transaction_type: TransactionType.RFC }) : creditorsApi.transactions.update(rfcId, data),
    onSuccess: () => {
      router.push('/dashboard/admin/creditors/transactions/rfc');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  const calculateLineValue = (item: RFCItem) => {
    return item.quantity * item.unit_value;
  };

  const calculateTotalValue = () => {
    return formData.items.reduce((sum, item) => sum + calculateLineValue(item), 0);
  };

  const addLineItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { stock_code: '', description: '', quantity: 0, unit_value: 0, return_reason: '' }],
    });
  };

  const removeLineItem = (index: number) => {
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index),
    });
  };

  const updateLineItem = (index: number, updates: Partial<RFCItem>) => {
    const newItems = [...formData.items];
    newItems[index] = { ...newItems[index], ...updates };
    setFormData({ ...formData, items: newItems });
  };

  if (isLoading && !isNew && rfcId !== 'edit') {
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
        <h1 className="text-3xl font-bold">{isNew ? 'New RFC' : 'RFC Details'}</h1>
        <p className="text-gray-600 mt-1">Track returns for credit from suppliers</p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* RFC Header */}
        <Card className="p-6 mb-6">
          <h2 className="text-lg font-bold mb-4">RFC Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Supplier</label>
              <select
                value={formData.supplier_id}
                onChange={(e) => setFormData({ ...formData, supplier_id: parseInt(e.target.value) })}
                className="w-full border border-gray-300 rounded px-3 py-2"
                required
                disabled={!isNew && !isEdit}
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
              <label className="block text-sm font-medium mb-1">RFC Date</label>
              <Input
                type="date"
                value={formData.rfc_date}
                onChange={(e) => setFormData({ ...formData, rfc_date: e.target.value })}
                required
                disabled={!isNew && !isEdit}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                className="w-full border border-gray-300 rounded px-3 py-2"
              >
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="credited">Credited</option>
                <option value="replaced">Stock Replaced</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Items */}
        <Card className="p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">Items for Return</h2>
            {(isNew || isEdit) && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addLineItem}
                className="flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Item
              </Button>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left font-semibold">Stock Code</th>
                  <th className="px-2 py-2 text-left font-semibold">Description</th>
                  <th className="px-2 py-2 text-left font-semibold">Return Reason</th>
                  <th className="px-2 py-2 text-right font-semibold">Qty</th>
                  <th className="px-2 py-2 text-right font-semibold">Unit Value</th>
                  <th className="px-2 py-2 text-right font-semibold">Total</th>
                  {(isNew || isEdit) && <th className="px-2 py-2 text-center font-semibold">Action</th>}
                </tr>
              </thead>
              <tbody>
                {formData.items.map((item, index) => (
                  <tr key={index} className="border-b">
                    <td className="px-2 py-2">
                      {isNew || isEdit ? (
                        <Input
                          type="text"
                          value={item.stock_code}
                          onChange={(e) => updateLineItem(index, { stock_code: e.target.value })}
                          className="text-xs"
                          placeholder="Stock code"
                        />
                      ) : (
                        <span>{item.stock_code}</span>
                      )}
                    </td>
                    <td className="px-2 py-2">
                      {isNew || isEdit ? (
                        <Input
                          type="text"
                          value={item.description}
                          onChange={(e) => updateLineItem(index, { description: e.target.value })}
                          className="text-xs"
                          placeholder="Description"
                        />
                      ) : (
                        <span>{item.description}</span>
                      )}
                    </td>
                    <td className="px-2 py-2">
                      {isNew || isEdit ? (
                        <select
                          value={item.return_reason}
                          onChange={(e) => updateLineItem(index, { return_reason: e.target.value })}
                          className="w-full border border-gray-300 rounded px-2 py-1 text-xs"
                        >
                          <option value="">Select reason...</option>
                          <option value="DEFECTIVE">Defective</option>
                          <option value="OVERSTOCK">Overstock</option>
                          <option value="WRONG_ITEM">Wrong Item</option>
                          <option value="NO_LONGER_NEEDED">Not Needed</option>
                          <option value="EXPIRED">Expired</option>
                        </select>
                      ) : (
                        <span>{item.return_reason}</span>
                      )}
                    </td>
                    <td className="px-2 py-2">
                      {isNew || isEdit ? (
                        <Input
                          type="number"
                          step="0.01"
                          value={item.quantity}
                          onChange={(e) => updateLineItem(index, { quantity: parseFloat(e.target.value) })}
                          className="text-xs text-right"
                        />
                      ) : (
                        <span className="text-right inline-block w-full">{item.quantity}</span>
                      )}
                    </td>
                    <td className="px-2 py-2">
                      {isNew || isEdit ? (
                        <Input
                          type="number"
                          step="0.01"
                          value={item.unit_value}
                          onChange={(e) => updateLineItem(index, { unit_value: parseFloat(e.target.value) })}
                          className="text-xs text-right"
                        />
                      ) : (
                        <span className="text-right inline-block w-full">R {item.unit_value.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}</span>
                      )}
                    </td>
                    <td className="px-2 py-2 text-right font-bold">
                      R {calculateLineValue(item).toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </td>
                    {(isNew || isEdit) && (
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
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Total */}
        <Card className="p-6 mb-6">
          <div className="flex justify-end">
            <div className="w-full md:w-72">
              <div className="flex justify-between">
                <span className="font-bold">Total RFC Value:</span>
                <span className="font-bold text-lg text-blue-600">
                  R {calculateTotalValue().toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* Actions */}
        {(isNew || isEdit) && (
          <div className="flex gap-2">
            <Button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? 'Saving...' : 'Save RFC'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
            >
              Cancel
            </Button>
          </div>
        )}
      </form>
    </div>
  );
}

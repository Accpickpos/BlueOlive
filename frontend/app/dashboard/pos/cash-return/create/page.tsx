'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { getApiErrorMessage } from '@/lib/api';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Plus, Trash2, AlertCircle } from 'lucide-react';

export default function CreateCashReturnPage() {
  const router = useRouter();
  const { user } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);

  const [formData, setFormData] = useState({
    return_date: new Date().toISOString().split('T')[0],
    original_sale_number: '',
    customer_name: '',
    line_items: [{ stock_code: '', description: '', qty: 1, price: 0, total: 0 }],
    return_total: 0,
    reason: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleLineItemChange = (index: number, field: string, value: any) => {
    const newItems = [...formData.line_items];
    newItems[index] = { ...newItems[index], [field]: value };
    
    if (field === 'qty' || field === 'price') {
      const qty = field === 'qty' ? value : newItems[index].qty;
      const price = field === 'price' ? value : newItems[index].price;
      newItems[index].total = qty * price;
    }
    
    const newData = { ...formData, line_items: newItems };
    newData.return_total = newData.line_items.reduce((sum, item) => sum + (item.total || 0), 0);
    setFormData(newData);
  };

  const addLineItem = () => {
    setFormData(prev => ({
      ...prev,
      line_items: [
        ...prev.line_items,
        { stock_code: '', description: '', qty: 1, price: 0, total: 0 }
      ]
    }));
  };

  const removeLineItem = (index: number) => {
    const newItems = formData.line_items.filter((_, i) => i !== index);
    const return_total = newItems.reduce((sum, item) => sum + (item.total || 0), 0);
    setFormData(prev => ({
      ...prev,
      line_items: newItems,
      return_total: return_total
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (!formData.original_sale_number) {
        setError('Please enter the original sale number');
        return;
      }
      if (!formData.reason) {
        setError('Please enter a reason for the return');
        return;
      }
      if (formData.line_items.length === 0 || formData.line_items.every((i) => !i.stock_code)) {
        setError('Please add at least one line item');
        return;
      }

      const returnNumber = `CR-${Date.now()}`;

      await posAPI.createCashReturn({
        return_number: returnNumber,
        return_date: formData.return_date,
        original_sale_number: formData.original_sale_number,
        customer_name: formData.customer_name,
        reason: formData.reason,
        lines: formData.line_items
          .filter((item) => item.stock_code)
          .map((item, index) => ({
            line_number: index + 1,
            stock_code: item.stock_code,
            description: item.description,
            quantity: item.qty,
            unit_price: item.price,
            tax_code: 1,
          })),
      });

      setSuccess(true);
      setTimeout(() => router.push('/dashboard/pos/cash-return'), 2000);
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to create cash return'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Link href="/dashboard/pos/cash-return">
            <Button variant="ghost" size="sm" className="gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Cash Return - Refund</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Error Alert */}
          {error && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="pt-6 flex gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                <p className="text-red-800">{error}</p>
              </CardContent>
            </Card>
          )}

          {/* Success Alert */}
          {success && (
            <Card className="border-green-200 bg-green-50">
              <CardContent className="pt-6">
                <p className="text-green-800">Cash return created successfully! Redirecting...</p>
              </CardContent>
            </Card>
          )}

          {/* Header Section */}
          <Card>
            <CardHeader>
              <CardTitle>Return Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Return Date
                  </label>
                  <Input
                    type="date"
                    name="return_date"
                    value={formData.return_date}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Customer Name
                  </label>
                  <Input
                    type="text"
                    name="customer_name"
                    placeholder="Optional"
                    value={formData.customer_name}
                    onChange={handleInputChange}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Original Sale Number *
                </label>
                <Input
                  type="text"
                  name="original_sale_number"
                  placeholder="e.g. CS-000123"
                  value={formData.original_sale_number}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reason *
                </label>
                <textarea
                  name="reason"
                  placeholder="Reason for the return"
                  rows={2}
                  value={formData.reason}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </CardContent>
          </Card>

          <p className="text-sm text-gray-500 -mt-2">
            Cash returns always refund from the till. To credit a debtor account or arrange a
            replacement instead, use a Credit Note.
          </p>

          {/* Items Returned Section */}
          <Card>
            <CardHeader>
              <CardTitle>Items Returned</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Stock Code</th>
                      <th className="text-left py-2">Description</th>
                      <th className="text-center py-2">Qty</th>
                      <th className="text-right py-2">Price</th>
                      <th className="text-right py-2">Total</th>
                      <th className="text-center py-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {formData.line_items.map((item, index) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="py-2">
                          <Input
                            type="text"
                            placeholder="Stock code"
                            value={item.stock_code}
                            onChange={(e) => handleLineItemChange(index, 'stock_code', e.target.value)}
                            className="w-full"
                            size={10}
                          />
                        </td>
                        <td className="py-2 px-2">
                          <Input
                            type="text"
                            placeholder="Description"
                            value={item.description}
                            onChange={(e) => handleLineItemChange(index, 'description', e.target.value)}
                            className="w-full"
                          />
                        </td>
                        <td className="py-2 px-2 text-center">
                          <Input
                            type="number"
                            min="1"
                            value={item.qty}
                            onChange={(e) => handleLineItemChange(index, 'qty', parseFloat(e.target.value))}
                            className="w-16 text-center"
                          />
                        </td>
                        <td className="py-2 px-2 text-right">
                          <Input
                            type="number"
                            step="0.01"
                            value={item.price}
                            onChange={(e) => handleLineItemChange(index, 'price', parseFloat(e.target.value))}
                            className="w-24 text-right"
                          />
                        </td>
                        <td className="py-2 px-2 text-right font-medium">
                          R{item.total?.toFixed(2) || '0.00'}
                        </td>
                        <td className="py-2 px-2 text-center">
                          <button
                            type="button"
                            onClick={() => removeLineItem(index)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <Button
                type="button"
                onClick={addLineItem}
                variant="outline"
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Line Item
              </Button>
            </CardContent>
          </Card>

          {/* Refund Summary */}
          <Card>
            <CardContent className="pt-6">
              <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                <p className="text-sm text-gray-600 mb-1">Total Refund Amount</p>
                <p className="text-3xl font-bold text-red-900">R{formData.return_total.toFixed(2)}</p>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex justify-between gap-4">
            <Link href="/dashboard/pos/cash-return">
              <Button variant="outline">Cancel</Button>
            </Link>
            <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
              {loading ? 'Processing...' : 'Process Return'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

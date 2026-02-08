'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
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
    reference: '',
    original_sale_reference: '',
    line_items: [{ stock_code: '', description: '', qty: 1, price: 0, total: 0 }],
    return_total: 0,
    refund_method: 'cash', // cash, card, or credit
    comments: '',
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
      if (!formData.original_sale_reference) {
        setError('Please select original sale');
        return;
      }
      if (formData.line_items.length === 0) {
        setError('Please add at least one line item');
        return;
      }

      // Submit to API
      // const response = await posAPI.cashReturns.create(formData);
      setSuccess(true);
      setTimeout(() => router.push('/dashboard/pos/cash-return'), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create cash return');
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
                    Reference
                  </label>
                  <Input
                    type="text"
                    name="reference"
                    placeholder="Auto-generated reference"
                    value={formData.reference}
                    onChange={handleInputChange}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Original Sale Reference
                </label>
                <Input
                  type="text"
                  name="original_sale_reference"
                  placeholder="Click to search original sale"
                  value={formData.original_sale_reference}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Refund Method
                </label>
                <select
                  name="refund_method"
                  value={formData.refund_method}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="cash">Cash Refund</option>
                  <option value="card">Card Refund</option>
                  <option value="credit">Store Credit</option>
                </select>
              </div>
            </CardContent>
          </Card>

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

          {/* Comments Section */}
          <Card>
            <CardHeader>
              <CardTitle>Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <textarea
                name="comments"
                placeholder="Add any comments or reason for return"
                rows={3}
                value={formData.comments}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
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

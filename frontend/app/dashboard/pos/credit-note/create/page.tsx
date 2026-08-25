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

export default function CreateCreditNotePage() {
  const router = useRouter();
  const { user } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);

  const [formData, setFormData] = useState({
    credit_date: new Date().toISOString().split('T')[0],
    customer_name: '',
    debtor_account: '',
    original_sale_number: '',
    refund_type: 'CASH',
    reason: '',
    line_items: [{ stock_code: '', description: '', qty: 1, price: 0, total: 0 }],
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

    setFormData(prev => ({ ...prev, line_items: newItems }));
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
    setFormData(prev => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (!formData.customer_name.trim()) {
        setError('Please enter a customer name');
        return;
      }
      if (formData.line_items.length === 0 || formData.line_items.every((i) => !i.stock_code && !i.description)) {
        setError('Please add at least one line item');
        return;
      }

      const creditNumber = `CN-${Date.now()}`;

      await posAPI.createCreditNote({
        credit_number: creditNumber,
        credit_date: formData.credit_date,
        customer_name: formData.customer_name,
        debtor_account: formData.debtor_account || undefined,
        original_sale_number: formData.original_sale_number || undefined,
        refund_type: formData.refund_type as 'CASH' | 'ACCOUNT' | 'REPLACEMENT',
        reason: formData.reason || undefined,
        lines: formData.line_items
          .filter((item) => item.description)
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
      setTimeout(() => router.push('/dashboard/pos/credit-note'), 2000);
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to create credit note'));
    } finally {
      setLoading(false);
    }
  };

  const grandTotal = formData.line_items.reduce((sum, item) => sum + (item.total || 0), 0);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Link href="/dashboard/pos/credit-note">
            <Button variant="ghost" size="sm" className="gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Create Credit Note</h1>
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
                <p className="text-green-800">Credit note created successfully! Redirecting...</p>
              </CardContent>
            </Card>
          )}

          {/* Header Section */}
          <Card>
            <CardHeader>
              <CardTitle>Credit Note Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Credit Note Date *
                  </label>
                  <Input
                    type="date"
                    name="credit_date"
                    value={formData.credit_date}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Debtor Account Number
                  </label>
                  <Input
                    type="text"
                    name="debtor_account"
                    placeholder="Optional"
                    value={formData.debtor_account}
                    onChange={handleInputChange}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Customer Name *
                </label>
                <Input
                  type="text"
                  name="customer_name"
                  placeholder="Customer name"
                  value={formData.customer_name}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Refund Type
                  </label>
                  <select
                    name="refund_type"
                    value={formData.refund_type}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="CASH">Cash</option>
                    <option value="ACCOUNT">Credit to Account</option>
                    <option value="REPLACEMENT">Replacement</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Original Invoice / Sale Number
                  </label>
                  <Input
                    type="text"
                    name="original_sale_number"
                    placeholder="Optional"
                    value={formData.original_sale_number}
                    onChange={handleInputChange}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reason
                </label>
                <textarea
                  name="reason"
                  rows={2}
                  placeholder="Explain the reason for the credit note"
                  value={formData.reason}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </CardContent>
          </Card>

          {/* Line Items Section */}
          <Card>
            <CardHeader>
              <CardTitle>Returned Items</CardTitle>
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

          {/* Totals Section */}
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-2">
                <div className="flex justify-between text-lg font-bold">
                  <span>Credit Note Total:</span>
                  <span>R{grandTotal.toFixed(2)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex justify-between gap-4">
            <Link href="/dashboard/pos/credit-note">
              <Button variant="outline">Cancel</Button>
            </Link>
            <div className="flex gap-4">
              <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
                {loading ? 'Creating...' : 'Create Credit Note'}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

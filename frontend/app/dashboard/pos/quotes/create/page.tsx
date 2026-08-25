'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { getApiErrorMessage } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowLeft, AlertCircle, CheckCircle, Plus, Trash2 } from 'lucide-react';

export default function CreateQuotationPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    quotation_number: '',
    customer_name: '',
    telephone: '',
    delivery_address: '',
    quote_date: new Date().toISOString().split('T')[0],
    expiry_date: '',
  });

  const [lineItems, setLineItems] = useState<any[]>([]);
  const [newItem, setNewItem] = useState({
    stock_code: '',
    description: '',
    quantity: '',
    unit_rate: '',
    discount_percent: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAddLineItem = () => {
    if (!newItem.description.trim() || !newItem.quantity || !newItem.unit_rate) {
      setError('Description, quantity, and unit rate are required');
      return;
    }

    const qty = parseFloat(newItem.quantity);
    const rate = parseFloat(newItem.unit_rate);
    const discount = parseFloat(newItem.discount_percent || '0');
    const subtotal = qty * rate;
    const discountAmount = (subtotal * discount) / 100;
    const amount = subtotal - discountAmount;

    const item = {
      id: Date.now(),
      stock_code: newItem.stock_code,
      description: newItem.description,
      quantity: qty,
      unit_rate: rate,
      discount_percent: discount,
      subtotal,
      discount_amount: discountAmount,
      amount,
    };

    setLineItems([...lineItems, item]);
    setNewItem({ stock_code: '', description: '', quantity: '', unit_rate: '', discount_percent: '' });
    setError(null);
  };

  const handleRemoveLineItem = (id: number) => {
    setLineItems(lineItems.filter((item) => item.id !== id));
  };

  const totals = {
    subtotal: lineItems.reduce((sum, item) => sum + item.subtotal, 0),
    discount: lineItems.reduce((sum, item) => sum + item.discount_amount, 0),
    total: lineItems.reduce((sum, item) => sum + item.amount, 0),
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (!formData.quotation_number.trim()) {
        throw new Error('Quotation number is required');
      }
      if (!formData.customer_name.trim()) {
        throw new Error('Customer name is required');
      }
      if (lineItems.length === 0) {
        throw new Error('At least one line item is required');
      }

      // Address textarea splits across up to 3x 25-char lines to match the
      // backend's address_line1/2/3 fields.
      const addressLines = formData.delivery_address
        .split('\n')
        .flatMap((line) => line.match(/.{1,25}/g) ?? [])
        .slice(0, 3);

      await posAPI.createQuotation({
        quotation_number: formData.quotation_number,
        quotation_date: formData.quote_date,
        expiry_date: formData.expiry_date,
        customer_name: formData.customer_name,
        telephone: formData.telephone,
        address_line1: addressLines[0] ?? '',
        address_line2: addressLines[1] ?? '',
        address_line3: addressLines[2] ?? '',
        lines: lineItems.map((item, index) => ({
          line_number: index + 1,
          stock_code: item.stock_code,
          description: item.description,
          quantity: item.quantity,
          unit_price: item.unit_rate,
          discount_percentage: item.discount_percent,
          tax_code: 1,
        })),
      });

      setSuccess('Quotation created successfully');
      setTimeout(() => router.push('/dashboard/pos/quotes'), 2000);
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to create quotation'));
    } finally {
      setLoading(false);
    }
  };

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
          <h1 className="text-2xl font-bold text-gray-900">Create Quotation</h1>
          <p className="text-sm text-gray-500">Create new customer quotation</p>
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
          {/* Quotation Header */}
          <Card>
            <CardHeader>
              <CardTitle>Quotation Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Quotation Number *
                  </label>
                  <Input
                    type="text"
                    name="quotation_number"
                    placeholder="QT-001"
                    value={formData.quotation_number}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Customer Name *
                  </label>
                  <Input
                    type="text"
                    name="customer_name"
                    placeholder="Customer name"
                    value={formData.customer_name}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Quote Date *
                  </label>
                  <Input
                    type="date"
                    name="quote_date"
                    value={formData.quote_date}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Delivery Address
                </label>
                <textarea
                  name="delivery_address"
                  placeholder="Delivery address"
                  value={formData.delivery_address}
                  onChange={handleChange}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Expiry Date *
                </label>
                <Input
                  type="date"
                  name="expiry_date"
                  value={formData.expiry_date}
                  onChange={handleChange}
                  required
                />
              </div>
            </CardContent>
          </Card>

          {/* Line Items */}
          <Card>
            <CardHeader>
              <CardTitle>Items</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-6 gap-3 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Stock Code
                  </label>
                  <Input
                    type="text"
                    placeholder="Optional"
                    value={newItem.stock_code}
                    onChange={(e) =>
                      setNewItem({ ...newItem, stock_code: e.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <Input
                    type="text"
                    placeholder="Item"
                    value={newItem.description}
                    onChange={(e) =>
                      setNewItem({ ...newItem, description: e.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Qty
                  </label>
                  <Input
                    type="number"
                    placeholder="0"
                    value={newItem.quantity}
                    onChange={(e) =>
                      setNewItem({ ...newItem, quantity: e.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Unit Rate
                  </label>
                  <Input
                    type="number"
                    placeholder="0.00"
                    step="0.01"
                    value={newItem.unit_rate}
                    onChange={(e) =>
                      setNewItem({ ...newItem, unit_rate: e.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Discount %
                  </label>
                  <Input
                    type="number"
                    placeholder="0"
                    step="0.01"
                    value={newItem.discount_percent || ''}
                    onChange={(e) =>
                      setNewItem({ ...newItem, discount_percent: e.target.value })
                    }
                  />
                </div>
                <div className="flex items-end">
                  <Button
                    type="button"
                    onClick={handleAddLineItem}
                    className="w-full bg-green-600 hover:bg-green-700"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {lineItems.length > 0 ? (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Stock Code</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead className="text-right">Qty</TableHead>
                        <TableHead className="text-right">Unit Rate</TableHead>
                        <TableHead className="text-right">Discount</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead className="w-10"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {lineItems.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell>{item.stock_code || '—'}</TableCell>
                          <TableCell>{item.description}</TableCell>
                          <TableCell className="text-right">{item.quantity}</TableCell>
                          <TableCell className="text-right">
                            R{item.unit_rate.toFixed(2)}
                          </TableCell>
                          <TableCell className="text-right">
                            {item.discount_percent}% (R{item.discount_amount.toFixed(2)})
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            R{item.amount.toFixed(2)}
                          </TableCell>
                          <TableCell className="text-center">
                            <button
                              type="button"
                              onClick={() => handleRemoveLineItem(item.id)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="bg-gray-50">
                        <TableCell colSpan={3}></TableCell>
                        <TableCell colSpan={2} className="text-right font-bold">
                          Subtotal:
                        </TableCell>
                        <TableCell className="text-right font-bold">
                          R{totals.subtotal.toFixed(2)}
                        </TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                      <TableRow className="bg-gray-50">
                        <TableCell colSpan={3}></TableCell>
                        <TableCell colSpan={2} className="text-right font-bold">
                          Total Discount:
                        </TableCell>
                        <TableCell className="text-right font-bold text-red-600">
                          -R{totals.discount.toFixed(2)}
                        </TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                      <TableRow className="bg-blue-50">
                        <TableCell colSpan={3}></TableCell>
                        <TableCell colSpan={2} className="text-right font-bold text-blue-900">
                          Total:
                        </TableCell>
                        <TableCell className="text-right font-bold text-lg text-blue-900">
                          R{totals.total.toFixed(2)}
                        </TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">No items added yet</p>
              )}
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
              {loading ? 'Saving...' : 'Create Quotation'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { getApiErrorMessage } from '@/lib/api';
import { DebtorPicker } from '@/components/pos/DebtorPicker';
import { StockItemPicker } from '@/components/pos/StockItemPicker';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowLeft, AlertCircle, CheckCircle, Plus, Trash2 } from 'lucide-react';

interface DraftLine {
  stock_code: string;
  description: string;
  quantity: number;
  unit_price: number;
  cost_price: number;
  tax_code: number;
}

export default function CreateLaybyePage() {
  const router = useRouter();
  const { user } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Manual §8 "Laybye Control": "The Expiry date defaults to 3 months from
  // laybye date and the deposit to [X]% of the Total Due; amend if
  // required." No configurable percentage exists anywhere in the system,
  // so 25% is a hardcoded starting default here.
  const DEFAULT_DEPOSIT_PERCENT = 0.25;

  const defaultExpiryDate = () => {
    const d = new Date();
    d.setMonth(d.getMonth() + 3);
    return d.toISOString().split('T')[0];
  };

  const [formData, setFormData] = useState({
    laybye_number: '',
    customer_name: '',
    telephone: '',
    deposit_amount: '',
    laybye_date: new Date().toISOString().split('T')[0],
    expiry_date: defaultExpiryDate(),
    item_description: '',
  });
  const [depositTouched, setDepositTouched] = useState(false);

  const [debtor, setDebtor] = useState<{ account_number: string; name: string } | null>(null);
  const [lines, setLines] = useState<DraftLine[]>([]);
  const [draftItem, setDraftItem] = useState<{
    stock_code: string;
    description: string;
    tax_code: number;
    cost_price: number;
  } | null>(null);
  const [draftQty, setDraftQty] = useState('1');
  const [draftPrice, setDraftPrice] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    if (name === 'deposit_amount') setDepositTouched(true);
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const addLine = () => {
    if (!draftItem) return;
    const qty = parseFloat(draftQty) || 0;
    const price = parseFloat(draftPrice) || 0;
    if (qty <= 0 || price < 0) return;

    setLines((prev) => [
      ...prev,
      {
        stock_code: draftItem.stock_code,
        description: draftItem.description,
        quantity: qty,
        unit_price: price,
        cost_price: draftItem.cost_price,
        tax_code: draftItem.tax_code,
      },
    ]);
    setDraftItem(null);
    setDraftQty('1');
    setDraftPrice('');
  };

  const removeLine = (index: number) => {
    setLines((prev) => prev.filter((_, i) => i !== index));
  };

  const subtotal = lines.reduce((sum, l) => sum + l.quantity * l.unit_price, 0);
  const vat = lines.reduce((sum, l) => sum + (l.tax_code === 1 ? l.quantity * l.unit_price * 0.14 : 0), 0);
  const totalAmount = subtotal + vat;
  const depositAmount = parseFloat(formData.deposit_amount) || 0;
  const outstandingBalance = totalAmount - depositAmount;

  // Keep the deposit at the default 25% of total as items are added,
  // until the user edits it directly — then leave their value alone.
  useEffect(() => {
    if (depositTouched) return;
    const defaultDeposit = totalAmount * DEFAULT_DEPOSIT_PERCENT;
    setFormData((prev) => ({
      ...prev,
      deposit_amount: totalAmount > 0 ? defaultDeposit.toFixed(2) : '',
    }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [totalAmount, depositTouched]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.customer_name.trim()) {
      setError('Customer name is required');
      return;
    }
    if (!formData.expiry_date) {
      setError('Expiry date is required');
      return;
    }
    if (lines.length === 0) {
      setError('Add at least one item to the laybye');
      return;
    }
    if (!formData.deposit_amount || depositAmount < 0) {
      setError('Enter the deposit amount');
      return;
    }

    setLoading(true);
    try {
      const rental = await posAPI.createLaybye({
        laybye_number: formData.laybye_number.trim() || undefined,
        customer_name: formData.customer_name,
        telephone: formData.telephone,
        laybye_date: formData.laybye_date,
        expiry_date: formData.expiry_date,
        deposit_amount: depositAmount,
        comment1: formData.item_description.slice(0, 30),
        debtor_account_number: debtor ? parseInt(debtor.account_number, 10) : undefined,
        lines: lines.map((l) => ({
          stock_code: l.stock_code,
          description: l.description,
          quantity: l.quantity,
          unit_price: l.unit_price,
          cost_price: l.cost_price,
          tax_code: l.tax_code,
        })),
      });

      setSuccess('Laybye created — items reserved into laybye stock');
      setTimeout(() => router.push(`/dashboard/pos/laybays`), 1500);
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to create laybye'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center gap-4">
        <button onClick={() => router.back()} className="text-blue-600 hover:text-blue-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Create Laybye</h1>
          <p className="text-sm text-gray-500">
            Items are reserved into laybye stock immediately and only leave the ledger
            once the laybye is cancelled (returned) or paid off (invoiced).
          </p>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6 flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <p className="text-red-800">{error}</p>
            </CardContent>
          </Card>
        )}

        {success && (
          <Card className="border-green-200 bg-green-50">
            <CardContent className="pt-6 flex gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
              <p className="text-green-800">{success}</p>
            </CardContent>
          </Card>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Customer Details */}
          <Card>
            <CardHeader>
              <CardTitle>Customer Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Laybye Number</label>
                  <Input
                    type="text"
                    name="laybye_number"
                    placeholder="Auto-generated if left blank"
                    value={formData.laybye_number}
                    onChange={handleChange}
                    disabled={loading}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Customer Name *</label>
                  <Input
                    type="text"
                    name="customer_name"
                    placeholder="Customer name"
                    value={formData.customer_name}
                    onChange={handleChange}
                    disabled={loading}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Telephone</label>
                  <Input
                    type="text"
                    name="telephone"
                    placeholder="Customer telephone"
                    value={formData.telephone}
                    onChange={handleChange}
                    disabled={loading}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Debtor Account (optional)
                  </label>
                  <DebtorPicker
                    onSelect={(d) => setDebtor({ account_number: d.account_number, name: d.name })}
                    placeholder={debtor ? debtor.name : 'Link an account to auto-invoice on final payment'}
                    disabled={loading}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
                <textarea
                  name="item_description"
                  placeholder="Optional notes (max 30 characters)"
                  value={formData.item_description}
                  onChange={handleChange}
                  rows={2}
                  maxLength={30}
                  disabled={loading}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </CardContent>
          </Card>

          {/* Line Items */}
          <Card>
            <CardHeader>
              <CardTitle>Items on Laybye</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-gray-600 mb-1">Stock Item</label>
                  <StockItemPicker
                    onSelect={(item) => {
                      setDraftItem({
                        stock_code: item.stock_code,
                        description: item.description,
                        tax_code: item.tax_code === 0 || item.tax_code === 'ZERO' ? 0 : 1,
                        cost_price: item.cost_price,
                      });
                      setDraftPrice(String(item.selling_price ?? ''));
                    }}
                    placeholder={draftItem ? draftItem.description : 'Search stock items...'}
                    disabled={loading}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Qty</label>
                  <Input
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={draftQty}
                    onChange={(e) => setDraftQty(e.target.value)}
                    disabled={loading}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Unit Price</label>
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    value={draftPrice}
                    onChange={(e) => setDraftPrice(e.target.value)}
                    disabled={loading}
                  />
                </div>
                <div className="md:col-span-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={addLine}
                    disabled={!draftItem || loading}
                    className="gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add Item
                  </Button>
                </div>
              </div>

              {lines.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-gray-600">
                        <th className="py-2">Stock Code</th>
                        <th className="py-2">Description</th>
                        <th className="py-2 text-right">Qty</th>
                        <th className="py-2 text-right">Price</th>
                        <th className="py-2 text-right">Line Total</th>
                        <th className="py-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {lines.map((l, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="py-2 font-mono">{l.stock_code}</td>
                          <td className="py-2">{l.description}</td>
                          <td className="py-2 text-right">{l.quantity}</td>
                          <td className="py-2 text-right">R{l.unit_price.toFixed(2)}</td>
                          <td className="py-2 text-right font-medium">
                            R{(l.quantity * l.unit_price).toFixed(2)}
                          </td>
                          <td className="py-2 text-center">
                            <button type="button" onClick={() => removeLine(idx)} className="text-red-500 hover:text-red-700">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {lines.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">No items added yet</p>
              )}
            </CardContent>
          </Card>

          {/* Deposit & Totals */}
          <Card>
            <CardHeader>
              <CardTitle>Deposit</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Laybye Date</label>
                  <Input type="date" name="laybye_date" value={formData.laybye_date} onChange={handleChange} disabled={loading} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Expiry Date *</label>
                  <Input type="date" name="expiry_date" value={formData.expiry_date} onChange={handleChange} disabled={loading} required />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Deposit Amount *</label>
                <Input
                  type="number"
                  name="deposit_amount"
                  placeholder="0.00"
                  step="0.01"
                  value={formData.deposit_amount}
                  onChange={handleChange}
                  disabled={loading}
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t">
                <div>
                  <p className="text-xs text-gray-500">Subtotal + VAT</p>
                  <p className="font-bold text-gray-900">R{totalAmount.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Deposit</p>
                  <p className="font-bold text-gray-900">R{depositAmount.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Outstanding</p>
                  <p className="font-bold text-blue-900">R{outstandingBalance.toFixed(2)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex gap-4 justify-end">
            <Button type="button" onClick={() => router.back()} variant="outline" disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={loading}>
              {loading ? 'Saving...' : 'Create Laybye'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

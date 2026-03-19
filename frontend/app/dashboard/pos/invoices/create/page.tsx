'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI, LineItem, InvoiceCreateData } from '@/lib/posApi';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Plus, Trash2, Check } from 'lucide-react';
import {
  ErrorAlert,
  SuccessAlert,
  LoadingOverlay,
  AccountInfoCard,
  TotalsSummary,
} from '@/components/pos/form-components';
import { DebtorPicker, StockItemPicker } from '@/components/pos';

export default function CreateInvoice() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  // FIX 1: stabilise API instance with useRef pattern (same fix as list page)
  const posAPI = usePOSAPI(user?.tenant?.slug);

  const [step, setStep] = useState<'debtor' | 'header' | 'items' | 'review'>('debtor');

  // Debtor
  const [selectedDebtor, setSelectedDebtor] = useState<any>(null);
  const [debtorError, setDebtorError] = useState<string | null>(null);

  // Header
  const [headerData, setHeaderData] = useState({
    invoice_date: new Date().toISOString().split('T')[0],
    delivery_date: '',
    delivery_details: '',
    reg_make_names: '',
    credit_card: '',
    order_number: '',
    customer_ref: '',
    notes: '',
  });

  // Line items
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [currentItem, setCurrentItem] = useState<Partial<LineItem>>({
    stock_code: '',
    item_code: '',
    description: '',
    quantity: 1,
    unit_price: 0,
    selling_price: 0,
    discount_percentage: 0,
    tax_code: 1,
    cost_price: 0,
  });

  // Form state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleHeaderChange = (field: string, value: string) => {
    setHeaderData((prev) => ({ ...prev, [field]: value }));
  };

  const handleAddLineItem = () => {
    const code = currentItem.stock_code || currentItem.item_code || '';
    if (!code || !currentItem.description || !currentItem.quantity) {
      setError('Please fill in the stock code, description and quantity');
      return;
    }
    const price = currentItem.unit_price || currentItem.selling_price || 0;
    if (price <= 0) {
      setError('Unit price must be greater than zero');
      return;
    }

    const newItem: LineItem = {
      stock_code: code,
      description: currentItem.description || '',
      quantity: Number(currentItem.quantity) || 0,
      unit_price: Number(price),
      discount_percentage: Number(currentItem.discount_percentage) || 0,
      tax_code: Number(currentItem.tax_code) ?? 1,
      cost_price: Number(currentItem.cost_price) || 0,
    };

    setLineItems((prev) => [...prev, newItem]);
    setCurrentItem({
      stock_code: '',
      item_code: '',
      description: '',
      quantity: 1,
      unit_price: 0,
      selling_price: 0,
      discount_percentage: 0,
      tax_code: 1,
      cost_price: 0,
    });
    setError(null);
  };

  const handleRemoveLineItem = (index: number) => {
    setLineItems((prev) => prev.filter((_, i) => i !== index));
  };

  const calculateTotals = () => {
    let subtotal = 0;
    let totalDiscount = 0;
    let totalTax = 0;

    lineItems.forEach((item) => {
      const itemSubtotal = Number(item.quantity) * Number(item.unit_price || 0);
      const discount = itemSubtotal * (Number(item.discount_percentage || 0) / 100);
      const afterDiscount = itemSubtotal - discount;
      // FIX 2: use 14% VAT to match backend, tax_code 1 = standard
      const taxRate = Number(item.tax_code) === 1 ? 0.14 : 0;
      const tax = afterDiscount * taxRate;
      subtotal += itemSubtotal;
      totalDiscount += discount;
      totalTax += tax;
    });

    return {
      subtotal,
      totalDiscount,
      totalTax,
      total: subtotal - totalDiscount + totalTax,
    };
  };

  const handleSubmitInvoice = async () => {
    if (!selectedDebtor) {
      setError('No debtor selected');
      return;
    }
    if (lineItems.length === 0) {
      setError('Please add at least one line item');
      return;
    }

    // FIX 3: debtor_account_number must be a string of the numeric dno field.
    // DebtorPicker returns the debtor object — use dno (the integer PK the backend expects).
    const accountNumber =
      selectedDebtor.dno != null
        ? String(selectedDebtor.dno)
        : selectedDebtor.account_number != null
        ? String(selectedDebtor.account_number)
        : null;

    if (!accountNumber) {
      setError('Could not determine debtor account number. Please re-select the customer.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Backend requires invoice_number — generate a unique one client-side (max 20 chars)
      const today = headerData.invoice_date.replace(/-/g, ''); // YYYYMMDD
      const rand  = Math.floor(Math.random() * 9999).toString().padStart(4, '0');
      const invoiceNumber = `INV-${today}-${rand}`; // e.g. INV-20250318-0042 (19 chars)

      const invoiceData: any = {
        debtor_account_number: accountNumber,
        invoice_number: invoiceNumber,
        invoice_date: headerData.invoice_date,
        // Backend requires 'lines' (not 'line_items') and each line needs a 'line_number'
        lines: lineItems.map((item, index) => ({
          line_number: index + 1,
          stock_code: item.stock_code || '',
          description: item.description || '',
          quantity: Number(item.quantity),
          unit_price: Number(item.unit_price || 0),
          discount_percentage: Number(item.discount_percentage || 0),
          tax_code: Number(item.tax_code ?? 1),
          cost_price: Number(item.cost_price || 0),
        })),
      };

      // Only include optional header fields that actually have values
      // Auto-set created_by to current logged-in user
      if (user?.username) {
        invoiceData.created_by = user.username;
      }
      if (headerData.delivery_date)    invoiceData.due_date      = headerData.delivery_date;
      if (headerData.order_number)     invoiceData.order_number  = headerData.order_number;
      if (headerData.customer_ref)     invoiceData.customer_reference = headerData.customer_ref;
      if (headerData.delivery_details) invoiceData.delivery_name = headerData.delivery_details;
      if (headerData.notes)            invoiceData.notes         = headerData.notes;

      // ── TEMP DEBUG: log exact payload so we can see what hits the backend ──
      console.log('=== INVOICE PAYLOAD ===');
      console.log(JSON.stringify(invoiceData, null, 2));
      console.log('debtor_account_number type:', typeof invoiceData.debtor_account_number, '| value:', invoiceData.debtor_account_number);
      console.log('lines count:', invoiceData.lines?.length);
      invoiceData.lines?.forEach((l: any, i: number) =>
        console.log(`  line[${i}]:`, JSON.stringify(l))
      );
      console.log('========================');

      const result = await posAPI.createInvoice(invoiceData);
      setSuccess('Invoice created successfully!');
      setTimeout(() => router.push('/dashboard/pos/invoices'), 2000);
    } catch (err: any) {
      console.error('Invoice creation error:', err);
      setError(err?.message || 'Failed to create invoice');
    } finally {
      setLoading(false);
    }
  };

  const totals = calculateTotals();

  if (authLoading) return <LoadingOverlay message="Loading..." />;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/dashboard/pos/invoices">
            <Button variant="ghost" size="icon" className="hover:bg-slate-200">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Create Invoice</h1>
            <p className="text-slate-600 mt-1">Invoice Option 1: Processing an Invoice</p>
          </div>
        </div>

        {/* Progress */}
        <div className="flex gap-4">
          {(['debtor', 'header', 'items', 'review'] as const).map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div
                className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                  step === s
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-200 text-slate-600'
                }`}
              >
                {i + 1}
              </div>
              <span className="text-sm font-medium text-slate-600 capitalize">{s}</span>
              {i < 3 && <div className="w-8 h-0.5 bg-slate-200" />}
            </div>
          ))}
        </div>

        {/* Alerts */}
        {error   && <ErrorAlert   message={error} />}
        {success && <SuccessAlert message={success} />}

        {/* ── Step 1: Debtor ────────────────────────────────────── */}
        {step === 'debtor' && (
          <Card>
            <CardHeader>
              <CardTitle>Step 1: Select Customer</CardTitle>
              <CardDescription>Search and select the customer for this invoice</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Customer</label>
                <DebtorPicker
                  onSelect={(debtor) => {
                    setSelectedDebtor(debtor);
                    setDebtorError(null);
                  }}
                  label="Customer"
                  placeholder="Search customers..."
                />
              </div>

              {selectedDebtor && (
                <AccountInfoCard
                  accountName={selectedDebtor.name || selectedDebtor.dname || ''}
                  accountNumber={
                    selectedDebtor.dno != null
                      ? String(selectedDebtor.dno)
                      : selectedDebtor.account_number || ''
                  }
                  balance={selectedDebtor.balance}
                  creditLimit={selectedDebtor.credit_limit}
                />
              )}

              {debtorError && <ErrorAlert message={debtorError} />}

              <div className="flex justify-end gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setSelectedDebtor(null)}
                >
                  Clear
                </Button>
                <Button
                  onClick={() => {
                    if (!selectedDebtor) { setDebtorError('Please select a customer'); return; }
                    setDebtorError(null);
                    setStep('header');
                  }}
                  disabled={!selectedDebtor}
                  className="bg-blue-600"
                >
                  <Check className="h-4 w-4 mr-2" />
                  Confirm &amp; Continue
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ── Step 2: Header ────────────────────────────────────── */}
        {step === 'header' && selectedDebtor && (
          <Card>
            <CardHeader>
              <CardTitle>Step 2: Invoice Header Details</CardTitle>
              <CardDescription>
                Customer: {selectedDebtor.name || selectedDebtor.dname}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Invoice Date *</label>
                  <Input
                    type="date"
                    value={headerData.invoice_date}
                    onChange={(e) => handleHeaderChange('invoice_date', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Due Date</label>
                  <Input
                    type="date"
                    value={headerData.delivery_date}
                    onChange={(e) => handleHeaderChange('delivery_date', e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Delivery Name / Details</label>
                <Input
                  placeholder="e.g., Building A, Floor 3"
                  value={headerData.delivery_details}
                  onChange={(e) => handleHeaderChange('delivery_details', e.target.value)}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Order Number</label>
                  <Input
                    placeholder="e.g., ORD-2025-001"
                    value={headerData.order_number}
                    onChange={(e) => handleHeaderChange('order_number', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Customer Reference</label>
                  <Input
                    placeholder="Customer ref"
                    value={headerData.customer_ref}
                    onChange={(e) => handleHeaderChange('customer_ref', e.target.value)}
                  />
                </div>
              </div>

              <div className="flex justify-between gap-2 pt-4">
                <Button variant="outline" onClick={() => setStep('debtor')}>Back</Button>
                <Button onClick={() => setStep('items')} className="bg-blue-600">
                  <Check className="h-4 w-4 mr-2" />
                  Continue to Items
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ── Step 3: Line Items ────────────────────────────────── */}
        {step === 'items' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Step 3: Add Line Items</CardTitle>
                <CardDescription>Search and add products to the invoice</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Select Product</label>
                  <StockItemPicker
                    onSelect={(item) => {
                      setCurrentItem({
                        stock_code: item.stock_code,
                        item_code:  item.stock_code,
                        description: item.description,
                        unit_price:    Number(item.selling_price || 0),
                        selling_price: Number(item.selling_price || 0),
                        cost_price:    Number(item.cost_price || 0),
                        // FIX 5: tax_code from stock item is already an integer; guard against string
                        tax_code: typeof item.tax_code === 'number'
                          ? item.tax_code
                          : item.tax_code_detail?.code === 'STANDARD' ? 1
                          : item.tax_code_detail?.code === 'REDUCED'  ? 2
                          : 0,
                        quantity: 1,
                        discount_percentage: 0,
                      });
                    }}
                    label="Product"
                    placeholder="Search products..."
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Stock Code</label>
                    <Input
                      value={currentItem.item_code || currentItem.stock_code || ''}
                      onChange={(e) => setCurrentItem({ ...currentItem, stock_code: e.target.value, item_code: e.target.value })}
                      placeholder="Code"
                    />
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <label className="text-sm font-medium">Description</label>
                    <Input
                      value={currentItem.description || ''}
                      onChange={(e) => setCurrentItem({ ...currentItem, description: e.target.value })}
                      placeholder="Description"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Qty</label>
                    <Input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={currentItem.quantity || ''}
                      onChange={(e) => setCurrentItem({ ...currentItem, quantity: parseFloat(e.target.value) || 0 })}
                      placeholder="1"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Unit Price (excl. VAT)</label>
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={currentItem.unit_price || currentItem.selling_price || ''}
                      onChange={(e) => {
                        const v = parseFloat(e.target.value) || 0;
                        setCurrentItem({ ...currentItem, unit_price: v, selling_price: v });
                      }}
                      placeholder="0.00"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Discount %</label>
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      value={currentItem.discount_percentage || ''}
                      onChange={(e) => setCurrentItem({ ...currentItem, discount_percentage: parseFloat(e.target.value) || 0 })}
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Tax Code</label>
                    <select
                      value={Number(currentItem.tax_code) ?? 1}
                      onChange={(e) => setCurrentItem({ ...currentItem, tax_code: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value={0}>Zero (0%)</option>
                      <option value={1}>Standard (14%)</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button onClick={handleAddLineItem} className="gap-2 bg-green-600 hover:bg-green-700">
                    <Plus className="h-4 w-4" />
                    Add Item
                  </Button>
                </div>
              </CardContent>
            </Card>

            {lineItems.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Invoice Items ({lineItems.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50 border-b-2">
                        <tr>
                          <th className="px-4 py-2 text-left">Code</th>
                          <th className="px-4 py-2 text-left">Description</th>
                          <th className="px-4 py-2 text-center">Qty</th>
                          <th className="px-4 py-2 text-right">Unit Price</th>
                          <th className="px-4 py-2 text-right">Discount</th>
                          <th className="px-4 py-2 text-right">VAT</th>
                          <th className="px-4 py-2 text-right">Total</th>
                          <th className="px-4 py-2 text-center"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {lineItems.map((item, index) => {
                          const base     = Number(item.quantity) * Number(item.unit_price || 0);
                          const disc     = base * (Number(item.discount_percentage || 0) / 100);
                          const net      = base - disc;
                          const vat      = Number(item.tax_code) === 1 ? net * 0.14 : 0;
                          const total    = net + vat;
                          return (
                            <tr key={index} className="border-b hover:bg-slate-50">
                              <td className="px-4 py-2 font-mono text-xs">{item.stock_code}</td>
                              <td className="px-4 py-2">{item.description}</td>
                              <td className="px-4 py-2 text-center">{item.quantity}</td>
                              <td className="px-4 py-2 text-right">R{Number(item.unit_price || 0).toFixed(2)}</td>
                              <td className="px-4 py-2 text-right">{item.discount_percentage || 0}%</td>
                              <td className="px-4 py-2 text-right">R{vat.toFixed(2)}</td>
                              <td className="px-4 py-2 text-right font-semibold">R{total.toFixed(2)}</td>
                              <td className="px-4 py-2 text-center">
                                <button onClick={() => handleRemoveLineItem(index)} className="text-red-500 hover:text-red-700">
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            <TotalsSummary
              subtotal={totals.subtotal}
              discount={totals.totalDiscount}
              tax={totals.totalTax}
              total={totals.total}
            />

            <div className="flex justify-between gap-2">
              <Button variant="outline" onClick={() => setStep('header')}>Back</Button>
              <Button
                onClick={() => setStep('review')}
                disabled={lineItems.length === 0}
                className="bg-blue-600"
              >
                <Check className="h-4 w-4 mr-2" />
                Review Invoice
              </Button>
            </div>
          </div>
        )}

        {/* ── Step 4: Review ────────────────────────────────────── */}
        {step === 'review' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Step 4: Review &amp; Submit</CardTitle>
                <CardDescription>Verify all details before creating the invoice</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Customer */}
                <div>
                  <h3 className="font-semibold text-slate-900 mb-3">Customer</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">Account #</p>
                      <p className="font-medium">
                        {selectedDebtor?.dno ?? selectedDebtor?.account_number}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-500">Name</p>
                      <p className="font-medium">{selectedDebtor?.name || selectedDebtor?.dname}</p>
                    </div>
                  </div>
                </div>

                {/* Invoice details */}
                <div>
                  <h3 className="font-semibold text-slate-900 mb-3">Invoice Details</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">Invoice Date</p>
                      <p className="font-medium">{headerData.invoice_date}</p>
                    </div>
                    {headerData.delivery_date && (
                      <div>
                        <p className="text-slate-500">Due Date</p>
                        <p className="font-medium">{headerData.delivery_date}</p>
                      </div>
                    )}
                    {headerData.order_number && (
                      <div>
                        <p className="text-slate-500">Order #</p>
                        <p className="font-medium">{headerData.order_number}</p>
                      </div>
                    )}
                    {headerData.customer_ref && (
                      <div>
                        <p className="text-slate-500">Customer Ref</p>
                        <p className="font-medium">{headerData.customer_ref}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Items */}
                <div>
                  <h3 className="font-semibold text-slate-900 mb-3">Items ({lineItems.length})</h3>
                  <div className="border rounded-lg overflow-hidden">
                    {lineItems.map((item, index) => {
                      const base  = Number(item.quantity) * Number(item.unit_price || 0);
                      const disc  = base * (Number(item.discount_percentage || 0) / 100);
                      const net   = base - disc;
                      const vat   = Number(item.tax_code) === 1 ? net * 0.14 : 0;
                      const total = net + vat;
                      return (
                        <div key={index} className="p-3 border-b last:border-b-0 bg-slate-50">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-slate-900 font-mono text-sm">{item.stock_code}</p>
                              <p className="text-sm text-slate-600">{item.description}</p>
                              <p className="text-xs text-slate-500">
                                {item.quantity} × R{Number(item.unit_price || 0).toFixed(2)}
                                {Number(item.discount_percentage) > 0 && ` − ${item.discount_percentage}%`}
                              </p>
                            </div>
                            <p className="font-semibold text-slate-900">R{total.toFixed(2)}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Totals */}
                <div className="bg-blue-50 p-4 rounded-lg grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-slate-600">Subtotal</p>
                    <p className="font-semibold">R{totals.subtotal.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-slate-600">Discount</p>
                    <p className="font-semibold">R{totals.totalDiscount.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-slate-600">VAT (14%)</p>
                    <p className="font-semibold">R{totals.totalTax.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-slate-600 font-medium">Total</p>
                    <p className="font-bold text-blue-600 text-lg">R{totals.total.toFixed(2)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-between gap-2">
              <Button variant="outline" onClick={() => setStep('items')}>
                Back to Items
              </Button>
              <Button
                onClick={handleSubmitInvoice}
                disabled={loading}
                className="gap-2 bg-green-600 hover:bg-green-700"
              >
                {loading ? 'Creating...' : 'Create Invoice'}
              </Button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
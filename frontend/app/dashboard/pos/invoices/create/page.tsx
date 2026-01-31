'use client';

import { useState, useEffect } from 'react';
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
import {
  ArrowLeft,
  Plus,
  Trash2,
  Search,
  Check,
  AlertCircle,
} from 'lucide-react';
import {
  ErrorAlert,
  SuccessAlert,
  InfoAlert,
  LoadingOverlay,
  AccountInfoCard,
  TotalsSummary,
} from '@/components/pos/form-components';

export default function CreateInvoice() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const posAPI = usePOSAPI(user?.tenant?.slug);

  // Form sections state
  const [step, setStep] = useState<'debtor' | 'header' | 'items' | 'review'>('debtor');

  // Debtor info
  const [debtorSearch, setDebtorSearch] = useState('');
  const [debtors, setDebtors] = useState<any[]>([]);
  const [selectedDebtor, setSelectedDebtor] = useState<any>(null);
  const [debtorLoading, setDebtorLoading] = useState(false);
  const [debtorError, setDebtorError] = useState<string | null>(null);

  // Header fields
  const [headerData, setHeaderData] = useState({
    invoice_date: new Date().toISOString().split('T')[0],
    delivery_date: '',
    delivery_details: '',
    reg_make_names: '',
    credit_card: '',
    order_number: '',
    customer_ref: '',
    sman_area: '',
  });

  // Line items
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [currentItem, setCurrentItem] = useState<Partial<LineItem>>({
    item_code: '',
    description: '',
    quantity: 0,
    selling_price: 0,
    discount_percentage: 0,
    tax_code: 'STANDARD',
    cost_price: 0,
  });
  const [stocks, setStocks] = useState<any[]>([]);
  const [stockLoading, setStockLoading] = useState(false);

  // Form state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Simulate debtor search
  const handleDebtorSearch = async (query: string) => {
    setDebtorSearch(query);
    if (query.length < 2) {
      setDebtors([]);
      return;
    }

    try {
      setDebtorLoading(true);
      setDebtorError(null);
      const result = await posAPI.searchDebtors(query);
      const debtorList = result.results || [];
      setDebtors(debtorList);
    } catch (err) {
      setDebtorError('Failed to search debtors');
      setDebtors([]);
    } finally {
      setDebtorLoading(false);
    }
  };

  // Confirm debtor selection
  const handleConfirmDebtor = () => {
    if (!selectedDebtor) {
      setDebtorError('Please select a debtor');
      return;
    }
    setStep('header');
  };

  // Handle header field changes
  const handleHeaderChange = (field: string, value: string) => {
    setHeaderData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Load stocks for search
  const handleStockSearch = async (query: string) => {
    if (query.length < 2) {
      setStocks([]);
      return;
    }

    try {
      setStockLoading(true);
      const result = await posAPI.searchStock(query);
      const stockList = result.results || [];
      setStocks(stockList);
    } catch (err) {
      setError('Failed to search stocks');
      setStocks([]);
    } finally {
      setStockLoading(false);
    }
  };

  // Select stock item
  const handleSelectStock = (stock: any) => {
    setCurrentItem({
      ...currentItem,
      item_code: stock.item_code,
      description: stock.description,
      selling_price: stock.selling_price,
      cost_price: stock.cost_price,
    });
    setStocks([]);
  };

  // Add line item
  const handleAddLineItem = () => {
    if (!currentItem.item_code || !currentItem.description || !currentItem.quantity) {
      setError('Please fill all item fields');
      return;
    }

    const newItem: LineItem = {
      item_code: currentItem.item_code || '',
      description: currentItem.description || '',
      quantity: currentItem.quantity || 0,
      selling_price: currentItem.selling_price || 0,
      discount_percentage: currentItem.discount_percentage || 0,
      tax_code: (currentItem.tax_code as 'ZERO' | 'STANDARD' | 'REDUCED') || 'STANDARD',
      cost_price: currentItem.cost_price || 0,
    };

    setLineItems([...lineItems, newItem]);
    setCurrentItem({
      item_code: '',
      description: '',
      quantity: 0,
      selling_price: 0,
      discount_percentage: 0,
      tax_code: 'STANDARD',
      cost_price: 0,
    });
    setError(null);
  };

  // Remove line item
  const handleRemoveLineItem = (index: number) => {
    setLineItems(lineItems.filter((_, i) => i !== index));
  };

  // Calculate totals
  const calculateTotals = () => {
    let subtotal = 0;
    let totalDiscount = 0;
    let totalTax = 0;

    lineItems.forEach((item) => {
      const itemSubtotal = item.quantity * item.selling_price;
      const discount = itemSubtotal * ((item.discount_percentage || 0) / 100);
      const afterDiscount = itemSubtotal - discount;
      const taxRate = item.tax_code === 'STANDARD' ? 0.15 : item.tax_code === 'REDUCED' ? 0.05 : 0;
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

  // Handle form submission
  const handleSubmitInvoice = async () => {
    if (!selectedDebtor || lineItems.length === 0) {
      setError('Please complete all sections');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const invoiceData: InvoiceCreateData = {
        debtor_account_number: selectedDebtor.account_number,
        invoice_date: headerData.invoice_date,
        delivery_date: headerData.delivery_date || undefined,
        delivery_details: headerData.delivery_details || undefined,
        reg_make_names: headerData.reg_make_names || undefined,
        credit_card: headerData.credit_card || undefined,
        order_number: headerData.order_number || undefined,
        customer_ref: headerData.customer_ref || undefined,
        sman_area: headerData.sman_area || undefined,
        line_items: lineItems,
      };

      await posAPI.createInvoice(invoiceData);
      setSuccess('Invoice created successfully!');
      setTimeout(() => router.push('/dashboard/pos/invoices'), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create invoice');
    } finally {
      setLoading(false);
    }
  };

  const totals = calculateTotals();

  if (authLoading) {
    return <LoadingOverlay message="Loading..." />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
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
        </div>

        {/* Progress Indicator */}
        <div className="flex gap-4">
          {['debtor', 'header', 'items', 'review'].map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div
                className={`flex items-center justify-center w-8 h-8 rounded-full ${
                  step === s
                    ? 'bg-blue-600 text-white'
                    : ['debtor', 'header', 'items'].includes(s)
                    ? 'bg-slate-200 text-slate-600'
                    : 'bg-slate-100 text-slate-400'
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
        {error && <ErrorAlert message={error} />}
        {success && <SuccessAlert message={success} />}

        {/* Step 1: Debtor Selection */}
        {step === 'debtor' && (
          <Card>
            <CardHeader>
              <CardTitle>Step 1: Select Debtor</CardTitle>
              <CardDescription>Search and select the customer for this invoice</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Debtor Search */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Account Number or Name</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="Search debtors..."
                    value={debtorSearch}
                    onChange={(e) => handleDebtorSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Debtors List */}
              {debtors.length > 0 && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Available Debtors</label>
                  <div className="border rounded-lg overflow-hidden">
                    {debtors.map((debtor) => (
                      <div
                        key={debtor.account_number}
                        onClick={() => setSelectedDebtor(debtor)}
                        className={`p-4 cursor-pointer border-b last:border-b-0 transition ${
                          selectedDebtor?.account_number === debtor.account_number
                            ? 'bg-blue-50 border-l-4 border-blue-600'
                            : 'hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-semibold text-slate-900">{debtor.account_number}</p>
                            <p className="text-sm text-slate-600">{debtor.name}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-semibold text-slate-900">R{debtor.balance.toFixed(2)}</p>
                            <p className="text-xs text-slate-500">Balance</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Selected Debtor Info */}
              {selectedDebtor && (
                <AccountInfoCard
                  accountName={selectedDebtor.name}
                  accountNumber={selectedDebtor.account_number}
                  balance={selectedDebtor.balance}
                  creditLimit={selectedDebtor.credit_limit}
                />
              )}

              {debtorError && <ErrorAlert message={debtorError} />}

              {/* Action Buttons */}
              <div className="flex justify-end gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setDebtorSearch('');
                    setDebtors([]);
                    setSelectedDebtor(null);
                  }}
                >
                  Clear
                </Button>
                <Button onClick={handleConfirmDebtor} disabled={!selectedDebtor} className="bg-blue-600">
                  <Check className="h-4 w-4 mr-2" />
                  Confirm & Continue
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Header Details */}
        {step === 'header' && selectedDebtor && (
          <Card>
            <CardHeader>
              <CardTitle>Step 2: Invoice Header Details</CardTitle>
              <CardDescription>Customer: {selectedDebtor.name}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Row 1: Date fields */}
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
                  <label className="text-sm font-medium">Delivery Date</label>
                  <Input
                    type="date"
                    value={headerData.delivery_date}
                    onChange={(e) => handleHeaderChange('delivery_date', e.target.value)}
                  />
                </div>
              </div>

              {/* Row 2: Delivery details */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Delivery Details</label>
                <Input
                  placeholder="e.g., Building A, Floor 3"
                  value={headerData.delivery_details}
                  onChange={(e) => handleHeaderChange('delivery_details', e.target.value)}
                />
              </div>

              {/* Row 3: Reg/Make and Credit Card */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Reg/Make Names</label>
                  <Input
                    placeholder="e.g., ABC-123"
                    value={headerData.reg_make_names}
                    onChange={(e) => handleHeaderChange('reg_make_names', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Credit Card</label>
                  <Input
                    placeholder="Card details"
                    value={headerData.credit_card}
                    onChange={(e) => handleHeaderChange('credit_card', e.target.value)}
                  />
                </div>
              </div>

              {/* Row 4: Order and Customer Reference */}
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

              {/* Row 5: Salesman Area */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Salesman/Area</label>
                <Input
                  placeholder="e.g., North Region - John Smith"
                  value={headerData.sman_area}
                  onChange={(e) => handleHeaderChange('sman_area', e.target.value)}
                />
              </div>

              {/* Action Buttons */}
              <div className="flex justify-between gap-2 pt-4">
                <Button variant="outline" onClick={() => setStep('debtor')}>
                  Back
                </Button>
                <Button onClick={() => setStep('items')} className="bg-blue-600">
                  <Check className="h-4 w-4 mr-2" />
                  Continue to Items
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Line Items */}
        {step === 'items' && (
          <div className="space-y-6">
            {/* Add Item Section */}
            <Card>
              <CardHeader>
                <CardTitle>Step 3: Add Line Items</CardTitle>
                <CardDescription>Search and add products to the invoice</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Stock Search */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Stock Code or Description</label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      placeholder="Search products..."
                      onChange={(e) => handleStockSearch(e.target.value)}
                      className="pl-10"
                    />
                  </div>

                  {/* Stock suggestions dropdown */}
                  {stocks.length > 0 && (
                    <div className="border rounded-lg overflow-hidden bg-white">
                      {stocks.map((stock) => (
                        <div
                          key={stock.item_code}
                          onClick={() => handleSelectStock(stock)}
                          className="p-3 cursor-pointer border-b last:border-b-0 hover:bg-blue-50 transition"
                        >
                          <div className="flex justify-between">
                            <div>
                              <p className="font-medium text-slate-900">{stock.item_code}</p>
                              <p className="text-sm text-slate-600">{stock.description}</p>
                            </div>
                            <div className="text-right">
                              <p className="font-semibold text-slate-900">R{stock.selling_price}</p>
                              <p className="text-xs text-slate-500">QOH: {stock.quantity_on_hand}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Item Details Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Stock Code</label>
                    <Input
                      value={currentItem.item_code || ''}
                      onChange={(e) =>
                        setCurrentItem({
                          ...currentItem,
                          item_code: e.target.value,
                        })
                      }
                      placeholder="Code"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Description</label>
                    <Input
                      value={currentItem.description || ''}
                      onChange={(e) =>
                        setCurrentItem({
                          ...currentItem,
                          description: e.target.value,
                        })
                      }
                      placeholder="Description"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Qty</label>
                    <Input
                      type="number"
                      value={currentItem.quantity || ''}
                      onChange={(e) =>
                        setCurrentItem({
                          ...currentItem,
                          quantity: parseFloat(e.target.value) || 0,
                        })
                      }
                      placeholder="0"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Unit Price</label>
                    <Input
                      type="number"
                      value={currentItem.selling_price || ''}
                      onChange={(e) =>
                        setCurrentItem({
                          ...currentItem,
                          selling_price: parseFloat(e.target.value) || 0,
                        })
                      }
                      placeholder="0.00"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Discount %</label>
                    <Input
                      type="number"
                      value={currentItem.discount_percentage || ''}
                      onChange={(e) =>
                        setCurrentItem({
                          ...currentItem,
                          discount_percentage: parseFloat(e.target.value) || 0,
                        })
                      }
                      placeholder="0"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Tax Code</label>
                    <select
                      value={currentItem.tax_code || 'STANDARD'}
                      onChange={(e) =>
                        setCurrentItem({
                          ...currentItem,
                          tax_code: e.target.value as 'ZERO' | 'STANDARD' | 'REDUCED',
                        })
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="ZERO">Zero (0%)</option>
                      <option value="STANDARD">Standard (15%)</option>
                      <option value="REDUCED">Reduced (5%)</option>
                    </select>
                  </div>
                </div>

                {/* Add Item Button */}
                <div className="flex justify-end">
                  <Button onClick={handleAddLineItem} className="gap-2 bg-green-600 hover:bg-green-700">
                    <Plus className="h-4 w-4" />
                    Add Item
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Line Items Table */}
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
                          <th className="px-4 py-2 text-right">Tax</th>
                          <th className="px-4 py-2 text-right">Total</th>
                          <th className="px-4 py-2 text-center">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lineItems.map((item, index) => {
                          const subtotal = item.quantity * item.selling_price;
                          const discountAmount = subtotal * ((item.discount_percentage || 0) / 100);
                          const taxRate = item.tax_code === 'STANDARD' ? 0.15 : item.tax_code === 'REDUCED' ? 0.05 : 0;
                          const tax = (subtotal - discountAmount) * taxRate;
                          const total = subtotal - discountAmount + tax;

                          return (
                            <tr key={index} className="border-b hover:bg-slate-50">
                              <td className="px-4 py-2">{item.item_code}</td>
                              <td className="px-4 py-2">{item.description}</td>
                              <td className="px-4 py-2 text-center">{item.quantity}</td>
                              <td className="px-4 py-2 text-right">R{item.selling_price.toFixed(2)}</td>
                              <td className="px-4 py-2 text-right">{item.discount_percentage}%</td>
                              <td className="px-4 py-2 text-right">R{tax.toFixed(2)}</td>
                              <td className="px-4 py-2 text-right font-semibold">R{total.toFixed(2)}</td>
                              <td className="px-4 py-2 text-center">
                                <button
                                  onClick={() => handleRemoveLineItem(index)}
                                  className="text-red-600 hover:text-red-700"
                                >
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

            {/* Totals */}
            <TotalsSummary
              subtotal={totals.subtotal}
              discount={totals.totalDiscount}
              tax={totals.totalTax}
              total={totals.total}
            />

            {/* Navigation Buttons */}
            <div className="flex justify-between gap-2">
              <Button variant="outline" onClick={() => setStep('header')}>
                Back
              </Button>
              <Button onClick={() => setStep('review')} disabled={lineItems.length === 0} className="bg-blue-600">
                <Check className="h-4 w-4 mr-2" />
                Review Invoice
              </Button>
            </div>
          </div>
        )}

        {/* Step 4: Review */}
        {step === 'review' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Step 4: Review Invoice</CardTitle>
                <CardDescription>Verify all details before submitting</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Customer Info */}
                <div>
                  <h3 className="font-semibold text-slate-900 mb-3">Customer Information</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-sm">
                      <p className="text-slate-500">Account</p>
                      <p className="font-medium">{selectedDebtor.account_number}</p>
                    </div>
                    <div className="text-sm">
                      <p className="text-slate-500">Name</p>
                      <p className="font-medium">{selectedDebtor.name}</p>
                    </div>
                  </div>
                </div>

                {/* Invoice Details */}
                <div>
                  <h3 className="font-semibold text-slate-900 mb-3">Invoice Details</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">Invoice Date</p>
                      <p className="font-medium">{headerData.invoice_date}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Delivery Date</p>
                      <p className="font-medium">{headerData.delivery_date || 'N/A'}</p>
                    </div>
                    {headerData.order_number && (
                      <div>
                        <p className="text-slate-500">Order Number</p>
                        <p className="font-medium">{headerData.order_number}</p>
                      </div>
                    )}
                    {headerData.customer_ref && (
                      <div>
                        <p className="text-slate-500">Customer Ref</p>
                        <p className="font-medium">{headerData.customer_ref}</p>
                      </div>
                    )}
                    {headerData.sman_area && (
                      <div>
                        <p className="text-slate-500">Salesman/Area</p>
                        <p className="font-medium">{headerData.sman_area}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Items Summary */}
                <div>
                  <h3 className="font-semibold text-slate-900 mb-3">Items ({lineItems.length})</h3>
                  <div className="border rounded-lg overflow-hidden">
                    {lineItems.map((item, index) => {
                      const subtotal = item.quantity * item.selling_price;
                      const discountAmount = subtotal * ((item.discount_percentage || 0) / 100);
                      const taxRate = item.tax_code === 'STANDARD' ? 0.15 : item.tax_code === 'REDUCED' ? 0.05 : 0;
                      const tax = (subtotal - discountAmount) * taxRate;
                      const total = subtotal - discountAmount + tax;

                      return (
                        <div
                          key={index}
                          className="p-3 border-b last:border-b-0 bg-slate-50 hover:bg-slate-100"
                        >
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-slate-900">{item.item_code}</p>
                              <p className="text-sm text-slate-600">{item.description}</p>
                              <p className="text-xs text-slate-500">{item.quantity} × R{item.selling_price.toFixed(2)}</p>
                            </div>
                            <p className="font-semibold text-slate-900">R{total.toFixed(2)}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Final Totals */}
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-sm">
                      <p className="text-slate-600">Subtotal</p>
                      <p className="font-semibold text-slate-900">R{totals.subtotal.toFixed(2)}</p>
                    </div>
                    <div className="text-sm">
                      <p className="text-slate-600">Discount</p>
                      <p className="font-semibold text-slate-900">R{totals.totalDiscount.toFixed(2)}</p>
                    </div>
                    <div className="text-sm">
                      <p className="text-slate-600">Tax</p>
                      <p className="font-semibold text-slate-900">R{totals.totalTax.toFixed(2)}</p>
                    </div>
                    <div className="text-sm">
                      <p className="text-slate-600 font-medium">Total</p>
                      <p className="font-bold text-blue-600 text-lg">R{totals.total.toFixed(2)}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Navigation Buttons */}
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

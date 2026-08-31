'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Printer, Share2, Loader2, Mail, CheckCircle2, Percent, PencilLine } from 'lucide-react';
import { printInvoice, emailInvoice } from '@/lib/printUtils';
import { GrossProfitDisplay, GPBadge } from '@/components/pos/GrossProfitDisplay';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { TenderData } from '@/lib/posApi';

const TENDER_TYPES: { value: TenderData['tender_type']; label: string }[] = [
  { value: 'CASH', label: 'Cash' },
  { value: 'SPEEDPOINT', label: 'Card / Speedpoint' },
  { value: 'EFT', label: 'EFT' },
  { value: 'CHEQUE', label: 'Cheque' },
  { value: 'VOUCHER', label: 'Voucher' },
];

export default function InvoiceDetail() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  
  const [invoice, setInvoice] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [emailDialogOpen, setEmailDialogOpen] = useState(false);
  const [emailAddress, setEmailAddress] = useState('');
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [tenderType, setTenderType] = useState<TenderData['tender_type']>('CASH');
  const [paymentAmount, setPaymentAmount] = useState('');
  const [authorizationCode, setAuthorizationCode] = useState('');
  const [drawerName, setDrawerName] = useState('');
  const [bankName, setBankName] = useState('');
  const [recordingPayment, setRecordingPayment] = useState(false);
  const [payError, setPayError] = useState<string | null>(null);

  // Manual §1 "Invoice - Subtotal Discount Facility"
  const [discountDialogOpen, setDiscountDialogOpen] = useState(false);
  const [discountPercentage, setDiscountPercentage] = useState('');
  const [applyingDiscount, setApplyingDiscount] = useState(false);
  const [discountError, setDiscountError] = useState<string | null>(null);

  // Manual §1 "Invoice - Set Selling Price Facility"
  const [setPriceDialogOpen, setSetPriceDialogOpen] = useState(false);
  const [targetTotal, setTargetTotal] = useState('');
  const [applyingSetPrice, setApplyingSetPrice] = useState(false);
  const [setPriceError, setSetPriceError] = useState<string | null>(null);

  // Manual §1 "H" header re-display/edit facility
  const [headerDialogOpen, setHeaderDialogOpen] = useState(false);
  const [headerForm, setHeaderForm] = useState({
    invoice_date: '',
    due_date: '',
    delivery_name: '',
    order_number: '',
    customer_reference: '',
  });
  const [savingHeader, setSavingHeader] = useState(false);
  const [headerError, setHeaderError] = useState<string | null>(null);

  const invoiceId = params?.id as string;

  useEffect(() => {
    if (!user || authLoading) return;
    
    loadInvoice();
  }, [user, authLoading, invoiceId]);

  const loadInvoice = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await posAPI.getInvoice(invoiceId);
      setInvoice(response);
    } catch (err: any) {
      console.error('Error loading invoice:', err);
      setError(err.message || 'Failed to load invoice');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailInvoice = async () => {
    if (!emailAddress || !invoice) return;
    
    setSendingEmail(true);
    try {
      const result = await emailInvoice(invoice, emailAddress);
      if (result.success) {
        setEmailSent(true);
        setTimeout(() => {
          setEmailDialogOpen(false);
          setEmailSent(false);
          setEmailAddress('');
        }, 2000);
      } else {
        alert(result.message);
      }
    } catch (err: any) {
      console.error('Error sending email:', err);
      alert(err.message || 'Failed to send email');
    } finally {
      setSendingEmail(false);
    }
  };

  const openPaymentDialog = () => {
    if (!invoice) return;
    const balanceDue = Number(invoice.balance_due ?? invoice.total_amount ?? 0);
    setTenderType('CASH');
    setPaymentAmount(balanceDue.toFixed(2));
    setAuthorizationCode('');
    setDrawerName('');
    setBankName('');
    setPayError(null);
    setPaymentDialogOpen(true);
  };

  const handleRecordPayment = async () => {
    if (!invoice) return;

    const amount = Number(paymentAmount);
    if (!amount || amount <= 0) {
      setPayError('Enter a valid payment amount');
      return;
    }

    setRecordingPayment(true);
    setPayError(null);
    try {
      if (!invoice.is_posted && invoice.status === 'DRAFT') {
        await posAPI.postInvoice(invoiceId);
      }

      const tender: TenderData = { tender_type: tenderType, amount };
      if (tenderType === 'SPEEDPOINT' && authorizationCode) {
        tender.authorization_code = authorizationCode;
      }
      if (tenderType === 'CHEQUE') {
        if (drawerName) tender.drawer_name = drawerName;
        if (bankName) tender.bank_name = bankName;
      }

      await posAPI.tenderInvoice(invoiceId, [tender]);

      setPaymentDialogOpen(false);
      await loadInvoice();
    } catch (err: any) {
      console.error('Error recording payment:', err);
      setPayError(err.message || 'Failed to record payment');
    } finally {
      setRecordingPayment(false);
    }
  };

  const handleApplyDiscount = async () => {
    const percentage = Number(discountPercentage);
    if (Number.isNaN(percentage)) {
      setDiscountError('Enter a valid discount percentage');
      return;
    }
    setApplyingDiscount(true);
    setDiscountError(null);
    try {
      await posAPI.applySubtotalDiscountToInvoice(invoiceId, percentage);
      setDiscountDialogOpen(false);
      setDiscountPercentage('');
      await loadInvoice();
    } catch (err: any) {
      console.error('Error applying subtotal discount:', err);
      setDiscountError(err.message || 'Failed to apply discount');
    } finally {
      setApplyingDiscount(false);
    }
  };

  const handleApplySetPrice = async () => {
    const target = Number(targetTotal);
    if (!target || target <= 0) {
      setSetPriceError('Enter a valid total amount');
      return;
    }
    setApplyingSetPrice(true);
    setSetPriceError(null);
    try {
      await posAPI.applySetPriceOnInvoice(invoiceId, target);
      setSetPriceDialogOpen(false);
      setTargetTotal('');
      await loadInvoice();
    } catch (err: any) {
      console.error('Error setting invoice total:', err);
      setSetPriceError(err.message || 'Failed to set price');
    } finally {
      setApplyingSetPrice(false);
    }
  };

  const openHeaderDialog = () => {
    if (!invoice) return;
    setHeaderForm({
      invoice_date: invoice.invoice_date || '',
      due_date: invoice.due_date || '',
      delivery_name: invoice.delivery_name || '',
      order_number: invoice.order_number || '',
      customer_reference: invoice.customer_reference || '',
    });
    setHeaderError(null);
    setHeaderDialogOpen(true);
  };

  const handleSaveHeader = async () => {
    setSavingHeader(true);
    setHeaderError(null);
    try {
      // posApi's partialUpdateInvoice is typed against InvoiceCreateData,
      // which doesn't include due_date/delivery_name/customer_reference
      // under those exact names — the backend serializer does, so this
      // bypasses the (incomplete) TS shape rather than sending wrong keys.
      await posAPI.partialUpdateInvoice(invoiceId, headerForm as any);
      setHeaderDialogOpen(false);
      await loadInvoice();
    } catch (err: any) {
      console.error('Error saving invoice header:', err);
      setHeaderError(err.message || 'Failed to save header');
    } finally {
      setSavingHeader(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <p>{error}</p>
            <Button 
              variant="link" 
              onClick={() => router.push('/dashboard/pos/invoices')}
              className="text-red-700 p-0 h-auto mt-2"
            >
              Back to Invoices
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <p className="text-slate-500">Invoice not found</p>
            <Button 
              variant="link" 
              onClick={() => router.push('/dashboard/pos/invoices')}
              className="mt-2"
            >
              Back to Invoices
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const lineItems = invoice.line_items || [];
  const subtotal = lineItems.reduce((sum: number, item: any) => {
    const itemTotal = (item.quantity || 0) * (item.unit_price || item.selling_price || 0);
    const discount = itemTotal * ((item.discount_percentage || 0) / 100);
    return sum + itemTotal - discount;
  }, 0);
  
  const tax = Number(invoice.tax_amount) || 0;
  const total = Number(invoice.total_amount) || Number(subtotal) + tax;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard/pos/invoices">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Invoice {invoice.invoice_number}
              </h1>
              <p className="text-sm text-slate-500 mt-0.5">
                {invoice.status === 'PAID'
                  ? 'Paid'
                  : invoice.status === 'PARTIAL_PAID'
                  ? 'Partially Paid'
                  : invoice.is_cancelled || invoice.status === 'CANCELLED' || invoice.status === 'VOID'
                  ? 'Cancelled'
                  : invoice.is_posted
                  ? 'Posted'
                  : 'Pending'}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {invoice.status !== 'PAID' &&
              invoice.status !== 'CANCELLED' &&
              invoice.status !== 'VOID' && (
                <Button variant="default" size="sm" onClick={openPaymentDialog}>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Record Payment
                </Button>
              )}
            {invoice.status === 'DRAFT' && (
              <>
                <Button variant="outline" size="sm" onClick={openHeaderDialog}>
                  <PencilLine className="h-4 w-4 mr-2" />
                  Edit Header
                </Button>
                <Button variant="outline" size="sm" onClick={() => { setDiscountError(null); setDiscountDialogOpen(true); }}>
                  <Percent className="h-4 w-4 mr-2" />
                  Subtotal Discount
                </Button>
                <Button variant="outline" size="sm" onClick={() => { setSetPriceError(null); setTargetTotal(total ? total.toFixed(2) : ''); setSetPriceDialogOpen(true); }}>
                  Set Price
                </Button>
              </>
            )}
            <Button variant="outline" size="sm" onClick={() => printInvoice(invoice)}>
              <Printer className="h-4 w-4 mr-2" />
              Print
            </Button>
            <Button variant="outline" size="sm" onClick={() => setEmailDialogOpen(true)}>
              <Share2 className="h-4 w-4 mr-2" />
              Share
            </Button>
          </div>
        </div>

        {/* Invoice Details */}
        <Card>
          <CardHeader>
            <CardTitle>Invoice Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-slate-500">Invoice Date</p>
                <p className="font-medium">{invoice.invoice_date}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Due Date</p>
                <p className="font-medium">{invoice.due_date || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Customer</p>
                <p className="font-medium">{invoice.debtor_name || invoice.debtor?.name || invoice.debtor_account_number || 'Unknown'}</p>
              </div>
              {invoice.customer_reference && (
                <div>
                  <p className="text-sm text-slate-500">Customer Ref</p>
                  <p className="font-medium">{invoice.customer_reference}</p>
                </div>
              )}
              {invoice.order_number && (
                <div>
                  <p className="text-sm text-slate-500">Order Number</p>
                  <p className="font-medium">{invoice.order_number}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-slate-500">Total</p>
                <p className="font-bold text-lg">R{total.toFixed(2)}</p>
              </div>
              {invoice.gross_profit !== undefined && (
                <div>
                  <p className="text-sm text-slate-500">Gross Profit</p>
                  <GrossProfitDisplay
                    sellingPrice={Number(invoice.subtotal) || 0}
                    costPrice={Number(invoice.total_cost) || 0}
                    quantity={1}
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Line Items */}
        <Card>
          <CardHeader>
            <CardTitle>Line Items</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium text-slate-600">Item</th>
                    <th className="text-center py-3 px-4 font-medium text-slate-600">Qty</th>
                    <th className="text-right py-3 px-4 font-medium text-slate-600">Unit Price</th>
                    <th className="text-right py-3 px-4 font-medium text-slate-600">Discount</th>
                    <th className="text-right py-3 px-4 font-medium text-slate-600">Total</th>
                    <th className="text-right py-3 px-4 font-medium text-slate-600">GP</th>
                  </tr>
                </thead>
                <tbody>
                  {lineItems.map((item: any, index: number) => {
                    const itemTotal = (item.quantity || 0) * (item.unit_price || item.selling_price || 0);
                    const discount = itemTotal * ((item.discount_percentage || 0) / 100);
                    const lineTotal = itemTotal - discount;

                    return (
                      <tr key={index} className="border-b">
                        <td className="py-3 px-4">
                          <p className="font-medium">{item.stock_code || item.item_code || 'N/A'}</p>
                          <p className="text-sm text-slate-500">{item.description}</p>
                        </td>
                        <td className="text-center py-3 px-4">{item.quantity}</td>
                        <td className="text-right py-3 px-4">R{(item.unit_price || item.selling_price || 0).toFixed(2)}</td>
                        <td className="text-right py-3 px-4">{item.discount_percentage || 0}%</td>
                        <td className="text-right py-3 px-4 font-medium">R{lineTotal.toFixed(2)}</td>
                        <td className="text-right py-3 px-4">
                          {item.cost_price !== undefined && (
                            <GPBadge
                              sellingPrice={item.unit_price || item.selling_price || 0}
                              costPrice={item.cost_price || 0}
                              quantity={item.quantity || 1}
                            />
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={5} className="text-right py-3 px-4 font-medium">Subtotal</td>
                    <td className="text-right py-3 px-4">R{subtotal.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td colSpan={5} className="text-right py-3 px-4 font-medium">Tax</td>
                    <td className="text-right py-3 px-4">R{tax.toFixed(2)}</td>
                  </tr>
                  <tr className="border-t-2">
                    <td colSpan={5} className="text-right py-3 px-4 font-bold">Total</td>
                    <td className="text-right py-3 px-4 font-bold text-lg">R{total.toFixed(2)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Payment History */}
        {invoice.tenders && invoice.tenders.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Payment History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-4 font-medium text-slate-600">Date</th>
                      <th className="text-left py-2 px-4 font-medium text-slate-600">Method</th>
                      <th className="text-left py-2 px-4 font-medium text-slate-600">Reference</th>
                      <th className="text-right py-2 px-4 font-medium text-slate-600">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoice.tenders.map((t: any) => (
                      <tr key={t.id} className="border-b">
                        <td className="py-2 px-4 text-slate-600">
                          {t.created_at ? new Date(t.created_at).toLocaleDateString() : '—'}
                        </td>
                        <td className="py-2 px-4">{t.tender_type_display || t.tender_type}</td>
                        <td className="py-2 px-4 text-slate-500">
                          {t.authorization_code || t.drawer_name || '—'}
                        </td>
                        <td className="text-right py-2 px-4 font-medium">
                          R{Number(t.amount).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Notes */}
        {invoice.notes && (
          <Card>
            <CardHeader>
              <CardTitle>Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600">{invoice.notes}</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Email Dialog */}
      <Dialog open={emailDialogOpen} onOpenChange={setEmailDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Email Invoice</DialogTitle>
            <DialogDescription>
              Enter the email address to send this invoice to.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="email" className="text-right">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="customer@example.com"
                value={emailAddress}
                onChange={(e) => setEmailAddress(e.target.value)}
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEmailDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleEmailInvoice} 
              disabled={!emailAddress || sendingEmail}
            >
              {sendingEmail ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : emailSent ? (
                <>
                  <Mail className="h-4 w-4 mr-2" />
                  Sent!
                </>
              ) : (
                <>
                  <Mail className="h-4 w-4 mr-2" />
                  Send Email
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Record Payment Dialog */}
      <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Payment</DialogTitle>
            <DialogDescription>
              Capture how this invoice was paid. This creates a payment record you can review later.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="tender-type" className="text-right">
                Method
              </Label>
              <div className="col-span-3">
                <Select
                  value={tenderType}
                  onValueChange={(v) => setTenderType(v as TenderData['tender_type'])}
                >
                  <SelectTrigger id="tender-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TENDER_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="payment-amount" className="text-right">
                Amount
              </Label>
              <Input
                id="payment-amount"
                type="number"
                step="0.01"
                min="0"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                className="col-span-3"
              />
            </div>

            {tenderType === 'SPEEDPOINT' && (
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="auth-code" className="text-right">
                  Auth Code
                </Label>
                <Input
                  id="auth-code"
                  placeholder="Card authorization code"
                  value={authorizationCode}
                  onChange={(e) => setAuthorizationCode(e.target.value)}
                  className="col-span-3"
                />
              </div>
            )}

            {tenderType === 'CHEQUE' && (
              <>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="drawer-name" className="text-right">
                    Drawer Name
                  </Label>
                  <Input
                    id="drawer-name"
                    value={drawerName}
                    onChange={(e) => setDrawerName(e.target.value)}
                    className="col-span-3"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="bank-name" className="text-right">
                    Bank
                  </Label>
                  <Input
                    id="bank-name"
                    value={bankName}
                    onChange={(e) => setBankName(e.target.value)}
                    className="col-span-3"
                  />
                </div>
              </>
            )}

            {payError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                {payError}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPaymentDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleRecordPayment} disabled={recordingPayment}>
              {recordingPayment ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Recording...
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Record Payment
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Subtotal Discount Dialog — Manual §1 "Invoice - Subtotal Discount Facility" */}
      <Dialog open={discountDialogOpen} onOpenChange={setDiscountDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Apply Subtotal Discount</DialogTitle>
            <DialogDescription>
              Enter a discount % to apply to every line item. A negative value increases prices instead.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="discount-percentage" className="text-right">
                Discount %
              </Label>
              <Input
                id="discount-percentage"
                type="number"
                step="0.01"
                value={discountPercentage}
                onChange={(e) => setDiscountPercentage(e.target.value)}
                className="col-span-3"
              />
            </div>
            {discountError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                {discountError}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDiscountDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleApplyDiscount} disabled={applyingDiscount}>
              {applyingDiscount ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Applying...
                </>
              ) : (
                'Apply Discount'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Set Price Dialog — Manual §1 "Invoice - Set Selling Price Facility" */}
      <Dialog open={setPriceDialogOpen} onOpenChange={setSetPriceDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Set Invoice Total</DialogTitle>
            <DialogDescription>
              Enter the revised inclusive total. Every line's price is scaled proportionally to reach it.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="target-total" className="text-right">
                New Total
              </Label>
              <Input
                id="target-total"
                type="number"
                step="0.01"
                min="0"
                value={targetTotal}
                onChange={(e) => setTargetTotal(e.target.value)}
                className="col-span-3"
              />
            </div>
            {setPriceError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                {setPriceError}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSetPriceDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleApplySetPrice} disabled={applyingSetPrice}>
              {applyingSetPrice ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Applying...
                </>
              ) : (
                'Set Total'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Header Edit Dialog — Manual §1 "H" header re-display facility */}
      <Dialog open={headerDialogOpen} onOpenChange={setHeaderDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invoice Header</DialogTitle>
            <DialogDescription>Review or amend the invoice header details.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="header-invoice-date" className="text-right">
                Invoice Date
              </Label>
              <Input
                id="header-invoice-date"
                type="date"
                value={headerForm.invoice_date}
                onChange={(e) => setHeaderForm((f) => ({ ...f, invoice_date: e.target.value }))}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="header-due-date" className="text-right">
                Due Date
              </Label>
              <Input
                id="header-due-date"
                type="date"
                value={headerForm.due_date}
                onChange={(e) => setHeaderForm((f) => ({ ...f, due_date: e.target.value }))}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="header-delivery-name" className="text-right">
                Delivery Name
              </Label>
              <Input
                id="header-delivery-name"
                value={headerForm.delivery_name}
                onChange={(e) => setHeaderForm((f) => ({ ...f, delivery_name: e.target.value }))}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="header-order-number" className="text-right">
                Order Number
              </Label>
              <Input
                id="header-order-number"
                value={headerForm.order_number}
                onChange={(e) => setHeaderForm((f) => ({ ...f, order_number: e.target.value }))}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="header-customer-ref" className="text-right">
                Customer Ref
              </Label>
              <Input
                id="header-customer-ref"
                value={headerForm.customer_reference}
                onChange={(e) => setHeaderForm((f) => ({ ...f, customer_reference: e.target.value }))}
                className="col-span-3"
              />
            </div>
            {headerError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                {headerError}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setHeaderDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveHeader} disabled={savingHeader}>
              {savingHeader ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

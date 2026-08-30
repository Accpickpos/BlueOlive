'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import type { TenderData } from '@/lib/posApi';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2, FileCheck2, Receipt } from 'lucide-react';
import { DebtorPicker } from '@/components/pos/DebtorPicker';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const CONVERTED_STATUSES = ['CONVERTED_TO_INVOICE', 'INVOICED', 'CONVERTED_TO_CASH_SALE'];
const BLOCKED_STATUSES = ['CANCELLED', 'EXPIRED', ...CONVERTED_STATUSES, 'JOB'];

const TENDER_TYPES: { value: TenderData['tender_type']; label: string }[] = [
  { value: 'CASH', label: 'Cash' },
  { value: 'SPEEDPOINT', label: 'Card / Speedpoint' },
  { value: 'EFT', label: 'EFT' },
  { value: 'CHEQUE', label: 'Cheque' },
  { value: 'VOUCHER', label: 'Voucher' },
];

export default function QuoteDetail() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const posAPI = usePOSAPI(user?.tenant?.slug);

  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [convertDialogOpen, setConvertDialogOpen] = useState(false);
  const [selectedDebtor, setSelectedDebtor] = useState<{ account_number: string; name: string } | null>(null);
  const [tenderType, setTenderType] = useState<TenderData['tender_type']>('CASH');
  const [tenderAmount, setTenderAmount] = useState('');
  const [converting, setConverting] = useState<'invoice' | 'cash_sale' | null>(null);
  const [convertError, setConvertError] = useState<string | null>(null);

  const quoteId = params?.id as string;

  useEffect(() => {
    if (!user || authLoading) return;
    loadQuote();
  }, [user, authLoading, quoteId]);

  const loadQuote = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await posAPI.getQuotation(quoteId);
      setQuote(response);
    } catch (err: any) {
      console.error('Error loading quotation:', err);
      setError(err.message || 'Failed to load quotation');
    } finally {
      setLoading(false);
    }
  };

  const openConvertDialog = () => {
    if (!quote) return;
    setConvertError(null);
    setSelectedDebtor(
      quote.debtor_account
        ? { account_number: String(quote.debtor_account_number), name: quote.debtor_account_name }
        : null
    );
    setTenderType('CASH');
    setTenderAmount(Number(quote.total_amount || 0).toFixed(2));
    setConvertDialogOpen(true);
  };

  const handleConvertToInvoice = async () => {
    if (!quote) return;

    const debtorAccountNumber = quote.debtor_account
      ? String(quote.debtor_account_number)
      : selectedDebtor?.account_number;

    if (!debtorAccountNumber) {
      setConvertError('Select a customer before converting to an invoice');
      return;
    }

    setConverting('invoice');
    setConvertError(null);
    try {
      const result: any = await posAPI.convertQuotationToInvoice(quoteId, undefined, debtorAccountNumber);
      const invoiceId = result?.invoice?.id;
      if (invoiceId) {
        router.push(`/dashboard/pos/invoices/${invoiceId}`);
      } else {
        setConvertDialogOpen(false);
        await loadQuote();
      }
    } catch (err: any) {
      console.error('Error converting quotation:', err);
      setConvertError(err.message || 'Failed to convert quotation to invoice');
    } finally {
      setConverting(null);
    }
  };

  const handleConvertToCashSale = async () => {
    if (!quote) return;

    const amount = Number(tenderAmount);
    if (!amount || amount <= 0) {
      setConvertError('Enter a valid payment amount');
      return;
    }

    setConverting('cash_sale');
    setConvertError(null);
    try {
      const result: any = await posAPI.convertQuotationToCashSale(quoteId, [
        { tender_type: tenderType, amount },
      ]);
      const cashSaleId = result?.cash_sale?.id;
      if (cashSaleId) {
        router.push(`/dashboard/pos/cash-sales/${cashSaleId}`);
      } else {
        setConvertDialogOpen(false);
        await loadQuote();
      }
    } catch (err: any) {
      console.error('Error converting quotation to cash sale:', err);
      setConvertError(err.message || 'Failed to convert quotation to cash sale');
    } finally {
      setConverting(null);
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
              onClick={() => router.push('/dashboard/pos/quotes')}
              className="text-red-700 p-0 h-auto mt-2"
            >
              Back to Quotes
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!quote) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <p className="text-slate-500">Quotation not found</p>
            <Button variant="link" onClick={() => router.push('/dashboard/pos/quotes')} className="mt-2">
              Back to Quotes
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const lines = quote.lines || [];
  const canConvert = !BLOCKED_STATUSES.includes(quote.status);
  const alreadyConverted = CONVERTED_STATUSES.includes(quote.status);
  const hasDebtor = !!quote.debtor_account;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard/pos/quotes">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Quotation {quote.quotation_number}
              </h1>
              <p className="text-sm text-slate-500 mt-0.5">{quote.status_display || quote.status}</p>
            </div>
          </div>
          <div className="flex gap-2">
            {canConvert && !alreadyConverted && (
              <Button variant="default" size="sm" onClick={openConvertDialog}>
                <FileCheck2 className="h-4 w-4 mr-2" />
                Convert
              </Button>
            )}
          </div>
        </div>

        {alreadyConverted && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
            This quotation has already been {quote.status === 'CONVERTED_TO_CASH_SALE' ? 'converted to a cash sale' : 'converted to an invoice'}.
          </div>
        )}

        {/* Quotation Details */}
        <Card>
          <CardHeader>
            <CardTitle>Quotation Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-slate-500">Quotation Date</p>
                <p className="font-medium">{quote.quotation_date}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Expiry Date</p>
                <p className="font-medium">{quote.expiry_date || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Customer</p>
                <p className="font-medium">
                  {quote.debtor_account_name || quote.customer_name || 'Unknown'}
                </p>
                {quote.debtor_account_number ? (
                  <p className="text-xs text-slate-400">Account #{quote.debtor_account_number}</p>
                ) : (
                  <p className="text-xs text-slate-400">No debtor account (walk-in)</p>
                )}
              </div>
              {quote.telephone && (
                <div>
                  <p className="text-sm text-slate-500">Telephone</p>
                  <p className="font-medium">{quote.telephone}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-slate-500">Total</p>
                <p className="font-bold text-lg">R{Number(quote.total_amount || 0).toFixed(2)}</p>
              </div>
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
                  </tr>
                </thead>
                <tbody>
                  {lines.map((item: any, index: number) => (
                    <tr key={item.id ?? index} className="border-b">
                      <td className="py-3 px-4">
                        <p className="font-medium">{item.stock_code || 'N/A'}</p>
                        <p className="text-sm text-slate-500">{item.description}</p>
                      </td>
                      <td className="text-center py-3 px-4">{item.quantity}</td>
                      <td className="text-right py-3 px-4">R{Number(item.unit_price || 0).toFixed(2)}</td>
                      <td className="text-right py-3 px-4">{Number(item.discount_percentage || 0)}%</td>
                      <td className="text-right py-3 px-4 font-medium">R{Number(item.line_total || 0).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={4} className="text-right py-3 px-4 font-medium">Subtotal</td>
                    <td className="text-right py-3 px-4">R{Number(quote.subtotal || 0).toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td colSpan={4} className="text-right py-3 px-4 font-medium">VAT</td>
                    <td className="text-right py-3 px-4">R{Number(quote.vat_amount || 0).toFixed(2)}</td>
                  </tr>
                  <tr className="border-t-2">
                    <td colSpan={4} className="text-right py-3 px-4 font-bold">Total</td>
                    <td className="text-right py-3 px-4 font-bold text-lg">R{Number(quote.total_amount || 0).toFixed(2)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Convert Dialog */}
      <Dialog open={convertDialogOpen} onOpenChange={setConvertDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Convert Quotation</DialogTitle>
            <DialogDescription>
              {hasDebtor
                ? `This customer has a debtor account (${quote.debtor_account_name}, #${quote.debtor_account_number}) — convert to an invoice.`
                : 'This customer has no debtor account. Link one to invoice them on credit, or settle now as a cash sale.'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-5 py-2">
            {/* Invoice path */}
            <div className="space-y-2 border rounded-lg p-3">
              <p className="text-sm font-medium text-slate-700">Convert to Invoice</p>
              {!hasDebtor && (
                <DebtorPicker
                  onSelect={(debtor) => setSelectedDebtor({ account_number: debtor.account_number, name: debtor.name })}
                  label="Customer"
                />
              )}
              {!hasDebtor && selectedDebtor && (
                <p className="text-sm text-slate-500">
                  Selected: {selectedDebtor.name} (Account #{selectedDebtor.account_number})
                </p>
              )}
              <Button
                className="w-full"
                onClick={handleConvertToInvoice}
                disabled={converting !== null || (!hasDebtor && !selectedDebtor)}
              >
                {converting === 'invoice' ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Converting...
                  </>
                ) : (
                  <>
                    <FileCheck2 className="h-4 w-4 mr-2" />
                    Convert to Invoice
                  </>
                )}
              </Button>
            </div>

            {/* Cash sale path — only when there's no debtor to charge */}
            {!hasDebtor && (
              <div className="space-y-3 border rounded-lg p-3">
                <p className="text-sm font-medium text-slate-700">Or settle now as a Cash Sale</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="cs-tender-type" className="text-xs text-slate-500">Payment Method</Label>
                    <Select value={tenderType} onValueChange={(v) => setTenderType(v as TenderData['tender_type'])}>
                      <SelectTrigger id="cs-tender-type">
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
                  <div>
                    <Label htmlFor="cs-amount" className="text-xs text-slate-500">Amount</Label>
                    <Input
                      id="cs-amount"
                      type="number"
                      step="0.01"
                      min="0"
                      value={tenderAmount}
                      onChange={(e) => setTenderAmount(e.target.value)}
                    />
                  </div>
                </div>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleConvertToCashSale}
                  disabled={converting !== null}
                >
                  {converting === 'cash_sale' ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Converting...
                    </>
                  ) : (
                    <>
                      <Receipt className="h-4 w-4 mr-2" />
                      Convert to Cash Sale
                    </>
                  )}
                </Button>
              </div>
            )}

            {convertError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                {convertError}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setConvertDialogOpen(false)}>
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

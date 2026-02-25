'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Printer, Share2, Loader2 } from 'lucide-react';

export default function InvoiceDetail() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  
  const [invoice, setInvoice] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
  
  const tax = invoice.tax_amount || 0;
  const total = invoice.total_amount || subtotal + tax;

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
                {invoice.is_cancelled ? 'Cancelled' : invoice.is_posted ? 'Posted' : 'Pending'}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Printer className="h-4 w-4 mr-2" />
              Print
            </Button>
            <Button variant="outline" size="sm">
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
              {invoice.customer_ref && (
                <div>
                  <p className="text-sm text-slate-500">Customer Ref</p>
                  <p className="font-medium">{invoice.customer_ref}</p>
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
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={4} className="text-right py-3 px-4 font-medium">Subtotal</td>
                    <td className="text-right py-3 px-4">R{subtotal.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td colSpan={4} className="text-right py-3 px-4 font-medium">Tax</td>
                    <td className="text-right py-3 px-4">R{tax.toFixed(2)}</td>
                  </tr>
                  <tr className="border-t-2">
                    <td colSpan={4} className="text-right py-3 px-4 font-bold">Total</td>
                    <td className="text-right py-3 px-4 font-bold text-lg">R{total.toFixed(2)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>

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
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ArrowLeft, Loader2, CircleDollarSign, Ban } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const CLOSED_STATUSES = ['COMPLETED', 'CANCELLED', 'CONVERTED_TO_INVOICE', 'EXPIRED'];

export default function LaybyeDetail() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const posAPI = usePOSAPI(user?.tenant?.slug);

  const [laybye, setLaybye] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [recordingPayment, setRecordingPayment] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);

  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [retentionPercentage, setRetentionPercentage] = useState('0');
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  const laybyeId = params?.id as string;

  useEffect(() => {
    if (!user || authLoading) return;
    loadLaybye();
  }, [user, authLoading, laybyeId]);

  const loadLaybye = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await posAPI.getLaybye(laybyeId);
      setLaybye(response);
    } catch (err: any) {
      console.error('Error loading laybye:', err);
      setError(err.message || 'Failed to load laybye');
    } finally {
      setLoading(false);
    }
  };

  const openPaymentDialog = () => {
    if (!laybye) return;
    setPaymentError(null);
    setPaymentAmount(Number(laybye.balance_due || 0).toFixed(2));
    setPaymentDialogOpen(true);
  };

  const handleRecordPayment = async () => {
    if (!laybye) return;

    const amount = Number(paymentAmount);
    if (!amount || amount <= 0) {
      setPaymentError('Enter a valid payment amount');
      return;
    }
    if (amount > Number(laybye.balance_due || 0)) {
      setPaymentError(`Amount exceeds balance due (R${Number(laybye.balance_due).toFixed(2)})`);
      return;
    }

    setRecordingPayment(true);
    setPaymentError(null);
    try {
      const result: any = await posAPI.makePaymentOnLaybye(laybyeId, amount);
      setPaymentDialogOpen(false);
      if (result?.invoice_id) {
        router.push(`/dashboard/pos/invoices/${result.invoice_id}`);
      } else {
        await loadLaybye();
      }
    } catch (err: any) {
      console.error('Error recording laybye payment:', err);
      setPaymentError(err.message || 'Failed to record payment');
    } finally {
      setRecordingPayment(false);
    }
  };

  const handleCancelLaybye = async () => {
    if (!laybye) return;

    const retention = Number(retentionPercentage);
    if (Number.isNaN(retention) || retention < 0 || retention > 100) {
      setCancelError('Retention percentage must be between 0 and 100');
      return;
    }

    setCancelling(true);
    setCancelError(null);
    try {
      await posAPI.cancelLaybye(laybyeId, retention);
      setCancelDialogOpen(false);
      await loadLaybye();
    } catch (err: any) {
      console.error('Error cancelling laybye:', err);
      setCancelError(err.message || 'Failed to cancel laybye');
    } finally {
      setCancelling(false);
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
              onClick={() => router.push('/dashboard/pos/laybays')}
              className="text-red-700 p-0 h-auto mt-2"
            >
              Back to Laybays
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!laybye) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <p className="text-slate-500">Laybye not found</p>
            <Button variant="link" onClick={() => router.push('/dashboard/pos/laybays')} className="mt-2">
              Back to Laybays
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const lines = laybye.lines || [];
  const payments = laybye.payments || [];
  const isOpen = laybye.status === 'ACTIVE';
  const canCancel = isOpen;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard/pos/laybays">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Laybye {laybye.laybye_number}
              </h1>
              <p className="text-sm text-slate-500 mt-0.5">{laybye.status_display || laybye.status}</p>
            </div>
          </div>
          <div className="flex gap-2">
            {isOpen && (
              <Button variant="default" size="sm" onClick={openPaymentDialog}>
                <CircleDollarSign className="h-4 w-4 mr-2" />
                Record Payment
              </Button>
            )}
            {canCancel && (
              <Button variant="outline" size="sm" onClick={() => setCancelDialogOpen(true)}>
                <Ban className="h-4 w-4 mr-2" />
                Cancel Laybye
              </Button>
            )}
          </div>
        </div>

        {laybye.status === 'COMPLETED' && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
            This laybye is fully paid.
          </div>
        )}
        {laybye.status === 'CANCELLED' && (
          <div className="bg-slate-100 border border-slate-200 text-slate-600 px-4 py-3 rounded-lg text-sm">
            This laybye was cancelled{laybye.refund_amount ? ` — refund of R${Number(laybye.refund_amount).toFixed(2)} was calculated` : ''}.
          </div>
        )}

        {/* Laybye Details */}
        <Card>
          <CardHeader>
            <CardTitle>Laybye Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-slate-500">Laybye Date</p>
                <p className="font-medium">{laybye.laybye_date}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Expiry Date</p>
                <p className="font-medium">{laybye.expiry_date || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Customer</p>
                <p className="font-medium">{laybye.customer_name || 'Unknown'}</p>
                {laybye.debtor_account_number && (
                  <p className="text-xs text-slate-400">Account #{laybye.debtor_account_number}</p>
                )}
              </div>
              <div>
                <p className="text-sm text-slate-500">Total</p>
                <p className="font-bold text-lg">R{Number(laybye.total_amount || 0).toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Paid</p>
                <p className="font-bold text-lg text-green-600">R{Number(laybye.amount_paid || 0).toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Balance Due</p>
                <p className="font-bold text-lg text-red-600">R{Number(laybye.balance_due || 0).toFixed(2)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Line Items */}
        <Card>
          <CardHeader>
            <CardTitle>Items on Laybye</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2">Stock Code</th>
                    <th className="text-left py-2 px-2">Description</th>
                    <th className="text-right py-2 px-2">Qty</th>
                    <th className="text-right py-2 px-2">Price</th>
                    <th className="text-right py-2 px-2">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {lines
                    .filter((l: any) => l.transaction_type === 'SP')
                    .map((line: any, index: number) => (
                      <tr key={line.id ?? index} className="border-b">
                        <td className="py-2 px-2 font-mono">{line.stock_code}</td>
                        <td className="py-2 px-2">{line.description}</td>
                        <td className="py-2 px-2 text-right">{line.quantity}</td>
                        <td className="py-2 px-2 text-right">R{Number(line.unit_price || 0).toFixed(2)}</td>
                        <td className="py-2 px-2 text-right font-medium">
                          R{Number(line.line_total || 0).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Payment History */}
        <Card>
          <CardHeader>
            <CardTitle>Payment History</CardTitle>
          </CardHeader>
          <CardContent>
            {payments.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No payments recorded yet — only the initial deposit.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-2">Date</th>
                      <th className="text-right py-2 px-2">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.map((p: any) => (
                      <tr key={p.id} className="border-b">
                        <td className="py-2 px-2">{p.payment_date}</td>
                        <td className="py-2 px-2 text-right font-medium">R{Number(p.amount).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <p className="text-xs text-slate-400 mt-3">
              Deposit of R{Number(laybye.deposit_amount || 0).toFixed(2)} was recorded at creation and isn't listed as a separate payment here.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Record Payment Dialog */}
      <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Payment</DialogTitle>
            <DialogDescription>
              Balance due is R{Number(laybye.balance_due || 0).toFixed(2)}. Paying it off in full completes the
              laybye{laybye.debtor_account_number ? ' and automatically raises an invoice for it.' : '.'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="payment-amount" className="text-right">Amount</Label>
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
            {paymentError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                {paymentError}
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
                  <CircleDollarSign className="h-4 w-4 mr-2" />
                  Record Payment
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cancel Laybye Dialog */}
      <Dialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel Laybye</DialogTitle>
            <DialogDescription>
              This returns the reserved items to general stock. Enter what percentage of the amount paid
              should be retained (kept) rather than refunded.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="retention-pct" className="text-right">Retention %</Label>
              <Input
                id="retention-pct"
                type="number"
                min="0"
                max="100"
                step="1"
                value={retentionPercentage}
                onChange={(e) => setRetentionPercentage(e.target.value)}
                className="col-span-3"
              />
            </div>
            {cancelError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                {cancelError}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCancelDialogOpen(false)}>
              Back
            </Button>
            <Button variant="destructive" onClick={handleCancelLaybye} disabled={cancelling}>
              {cancelling ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Cancelling...
                </>
              ) : (
                <>
                  <Ban className="h-4 w-4 mr-2" />
                  Cancel Laybye
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

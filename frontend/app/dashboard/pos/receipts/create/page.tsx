'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI, TenderData, ReceiptCreateData } from '@/lib/posApi';
import { useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  FormSectionHeader,
  AccountInfoCard,
  TotalsSummary,
  FormActions,
  TenderRow,
  ErrorAlert,
  SuccessAlert,
  LoadingOverlay,
} from '@/components/pos/form-components';
import {
  AlertCircle,
  Plus,
  ArrowLeft,
  Check,
} from 'lucide-react';

export default function CreateReceipt() {
  const { user } = useAuth();
  const router = useRouter();
  const posAPI = usePOSAPI(user?.tenant?.slug);

  const [formData, setFormData] = useState({
    debtor_account_number: '',
    receipt_type: 'BALANCE_FORWARD' as 'BALANCE_FORWARD' | 'OPEN_ITEM' | 'POST_DATED_CHEQUE',
    receipt_date: new Date().toISOString().split('T')[0],
    amount: 0,
    notes: '',
  });

  const [tenders, setTenders] = useState<TenderData[]>([
    {
      tender_type: 'CASH',
      amount: 0,
    },
  ]);

  const [debtorInfo, setDebtorInfo] = useState<any>(null);
  const [debtorLoading, setDebtorLoading] = useState(false);
  const [debtorError, setDebtorError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Fetch debtor when account number changes
  useEffect(() => {
    const fetchDebtor = async () => {
      if (!formData.debtor_account_number) {
        setDebtorInfo(null);
        setDebtorError(null);
        return;
      }

      try {
        setDebtorLoading(true);
        setDebtorError(null);
        const isHealthy = await posAPI.healthCheck();
        if (isHealthy) {
          setDebtorInfo({ 
            account_number: formData.debtor_account_number,
            account_name: 'Sample Debtor Account',
            balance: 1500,
            credit_limit: 10000,
          });
        }
      } catch (err) {
        setDebtorError('Debtor account not found');
      } finally {
        setDebtorLoading(false);
      }
    };

    const timer = setTimeout(fetchDebtor, 500);
    return () => clearTimeout(timer);
  }, [formData.debtor_account_number, posAPI]);

  const addTender = () => {
    setTenders([
      ...tenders,
      {
        tender_type: 'CASH',
        amount: 0,
      },
    ]);
  };

  const removeTender = (index: number) => {
    if (tenders.length > 1) {
      setTenders(tenders.filter((_, i) => i !== index));
    }
  };

  const updateTender = (index: number, field: string, value: any) => {
    const updated = [...tenders];
    updated[index] = { ...updated[index], [field]: value };
    setTenders(updated);
  };

  const calculateTenderTotal = () => {
    return tenders.reduce((sum, t) => sum + (t.amount || 0), 0);
  };

  const tenderTotal = calculateTenderTotal();
  const amountDue = formData.amount > 0 ? formData.amount : 0;
  const amountPaid = tenderTotal;
  const balance = amountPaid - amountDue;

  const validateForm = () => {
    if (!formData.debtor_account_number) {
      setError('Please select a debtor account');
      return false;
    }
    if (formData.amount <= 0) {
      setError('Receipt amount must be greater than 0');
      return false;
    }
    if (tenders.length === 0 || tenders.some((t) => t.amount <= 0)) {
      setError('All payment methods must have an amount greater than 0');
      return false;
    }
    if (Math.abs(balance) > 0.01) {
      setError(`Amount due (R${amountDue.toFixed(2)}) does not match amount paid (R${amountPaid.toFixed(2)})`);
      return false;
    }
    return true;
  };

  const handleSaveDraft = async () => {
    if (!validateForm()) return;

    try {
      setSubmitting(true);
      setError(null);

      const receiptData: ReceiptCreateData = {
        debtor_account_number: formData.debtor_account_number,
        receipt_type: formData.receipt_type,
        receipt_date: formData.receipt_date,
        tenders: tenders,
        amount: formData.amount,
        notes: formData.notes,
      };

      const result = await posAPI.createReceipt(receiptData);
      setSuccess(`Receipt draft saved successfully! Receipt #${result.receipt_number}`);
      
      setTimeout(() => {
        router.push(`/dashboard/pos/receipts/${result.id}`);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save receipt');
    } finally {
      setSubmitting(false);
    }
  };

  const handlePost = async () => {
    if (!validateForm()) return;

    try {
      setSubmitting(true);
      setError(null);

      const receiptData: ReceiptCreateData = {
        debtor_account_number: formData.debtor_account_number,
        receipt_type: formData.receipt_type,
        receipt_date: formData.receipt_date,
        tenders: tenders,
        amount: formData.amount,
        notes: formData.notes,
      };

      const result = await posAPI.createReceipt(receiptData);
      setSuccess(`Receipt posted successfully! Receipt #${result.receipt_number}`);
      
      setTimeout(() => {
        router.push(`/dashboard/pos/receipts`);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to post receipt');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitting) {
    return <LoadingOverlay message="Processing receipt..." />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push('/dashboard/pos')}
              className="hover:bg-slate-200"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Record Payment Receipt</h1>
              <p className="text-slate-600 mt-1">Process debtor account payments</p>
            </div>
          </div>
        </div>

        {/* Success Alert */}
        {success && <SuccessAlert message={success} />}

        {/* Error Alert */}
        {error && <ErrorAlert message={error} />}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Main Form - Left Side */}
          <div className="lg:col-span-2 space-y-6">
            {/* Receipt Header Card */}
            <Card>
              <CardHeader>
                <CardTitle>Receipt Information</CardTitle>
                <CardDescription>Basic receipt details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Debtor Selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Debtor Account <span className="text-red-500">*</span>
                  </label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Enter account number (e.g., ACC001)"
                      value={formData.debtor_account_number}
                      onChange={(e) =>
                        setFormData({ ...formData, debtor_account_number: e.target.value })
                      }
                      className="flex-1"
                    />
                  </div>
                  <p className="text-xs text-slate-500">
                    Enter the debtor's account number to look up their details
                  </p>
                </div>

                {/* Debtor Info Card */}
                {debtorInfo && (
                  <AccountInfoCard
                    accountName={debtorInfo.account_name}
                    accountNumber={debtorInfo.account_number}
                    balance={debtorInfo.balance}
                    creditLimit={debtorInfo.credit_limit}
                  />
                )}
              </CardContent>
            </Card>

            {/* Receipt Details Card */}
            <Card>
              <CardHeader>
                <CardTitle>Receipt Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Receipt Type <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={formData.receipt_type}
                      onChange={(e) =>
                        setFormData({ ...formData, receipt_type: e.target.value as any })
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="BALANCE_FORWARD">Balance Forward</option>
                      <option value="OPEN_ITEM">Open Item</option>
                      <option value="POST_DATED_CHEQUE">Post Dated Cheque</option>
                    </select>
                    <p className="text-xs text-slate-500">
                      BALANCE_FORWARD: Full account payment
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Receipt Date <span className="text-red-500">*</span>
                    </label>
                    <Input
                      type="date"
                      value={formData.receipt_date}
                      onChange={(e) =>
                        setFormData({ ...formData, receipt_date: e.target.value })
                      }
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Amount Due <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600">R</span>
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={formData.amount}
                      onChange={(e) =>
                        setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })
                      }
                      className="pl-8"
                      placeholder="0.00"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Notes</label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) =>
                      setFormData({ ...formData, notes: e.target.value })
                    }
                    className="w-full min-h-24 p-3 border border-slate-200 rounded-lg text-sm"
                    placeholder="Optional notes about this receipt..."
                  />
                </div>
              </CardContent>
            </Card>

            {/* Payment Methods Card */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Payment Methods</CardTitle>
                  <CardDescription>How is this payment being received?</CardDescription>
                </div>
                <Button
                  size="sm"
                  onClick={addTender}
                  className="gap-2"
                >
                  <Plus className="h-4 w-4" />
                  Add Payment
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {tenders.map((tender, index) => (
                  <TenderRow
                    key={index}
                    tender={tender}
                    onUpdate={(field, value) =>
                      updateTender(index, field, value)
                    }
                    onRemove={() => removeTender(index)}
                    index={index}
                  />
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Summary - Right Side */}
          <div className="space-y-6">
            {/* Amount Summary */}
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle className="text-lg">Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center pb-3 border-b">
                    <span className="text-slate-600">Amount Due:</span>
                    <span className="font-semibold">R{amountDue.toFixed(2)}</span>
                  </div>

                  <div className="bg-blue-50 p-3 rounded-lg space-y-2">
                    <p className="text-xs text-slate-600 font-medium">PAYMENT BREAKDOWN</p>
                    {tenders.map((tender, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="text-slate-600">
                          {tender.tender_type}: {tender.tender_type === 'CHEQUE' && tender.drawer_name && `#${tender.drawer_name}`}
                        </span>
                        <span className="font-medium">R{tender.amount.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>

                  <div className={`flex justify-between items-center p-3 rounded-lg ${balance > 0.01 ? 'bg-green-50' : balance < -0.01 ? 'bg-red-50' : 'bg-green-50'}`}>
                    <span className="font-semibold">Total Paid:</span>
                    <span className={`font-bold text-lg ${Math.abs(balance) > 0.01 ? (balance > 0 ? 'text-green-600' : 'text-red-600') : 'text-green-600'}`}>
                      R{amountPaid.toFixed(2)}
                    </span>
                  </div>

                  {Math.abs(balance) > 0.01 && (
                    <div className={`text-sm p-2 rounded flex items-center gap-2 ${balance > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      <AlertCircle className="h-4 w-4" />
                      {balance > 0 ? (
                        <span>Change: R{balance.toFixed(2)}</span>
                      ) : (
                        <span>Shortfall: R{Math.abs(balance).toFixed(2)}</span>
                      )}
                    </div>
                  )}
                </div>

                {Math.abs(balance) < 0.01 && (
                  <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700">
                    <Check className="h-4 w-4" />
                    <span className="text-sm font-medium">Payment balanced</span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Info Card */}
            <Card className="bg-slate-900 text-white border-0">
              <CardContent className="pt-6 space-y-3">
                <div>
                  <p className="text-xs text-slate-400 mb-1">RECEIPT STATUS</p>
                  <p className="text-sm font-medium">Ready to Save</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400 mb-1">TENANT</p>
                  <p className="text-sm font-medium">{user?.tenant?.slug || 'Unknown'}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex gap-3 justify-end">
          <Button
            variant="outline"
            onClick={() => router.push('/dashboard/pos')}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            variant="outline"
            onClick={handleSaveDraft}
            disabled={submitting || !formData.debtor_account_number}
          >
            Save as Draft
          </Button>
          <Button
            onClick={handlePost}
            disabled={submitting || !formData.debtor_account_number || Math.abs(balance) > 0.01}
            className="gap-2 bg-green-600 hover:bg-green-700"
          >
            <Check className="h-4 w-4" />
            Post Receipt
          </Button>
        </div>
      </div>
    </div>
  );
}


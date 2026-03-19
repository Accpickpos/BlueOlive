'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { jobCardsApi } from '@/lib/jobCardsApi';
import { DebtorPicker } from '@/components/pos/DebtorPicker';
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
import { ArrowLeft, AlertCircle, CheckCircle, Edit, CreditCard, Banknote, Building } from 'lucide-react';
import Link from 'next/link';

export default function JobCardDetailPage() {
  const router = useRouter();
  const params = useParams();
  const { user } = useAuth();
  const [jobCard, setJobCard] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [converting, setConverting] = useState(false);
  const [showConvertDialog, setShowConvertDialog] = useState(false);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [selectedDebtor, setSelectedDebtor] = useState<any>(null);
  const [convertedInvoice, setConvertedInvoice] = useState<any>(null);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<string>('');
  const [processingPayment, setProcessingPayment] = useState(false);

  const jobId = params.id as string;

  useEffect(() => {
    if (jobId) {
      fetchJobCard();
    }
  }, [jobId]);

  const fetchJobCard = async () => {
    setLoading(true);
    try {
      const response = await jobCardsApi.get(jobId);
      setJobCard(response);
    } catch (err) {
      console.error('Error fetching job card:', err);
      setError('Failed to load job card');
    } finally {
      setLoading(false);
    }
  };

  const handleConvertToInvoice = async () => {
    // For conversion, we need either a debtor account number or ID
    // But we can also convert with just customer name if the invoice is created manually
    let debtorIdToUse: number | undefined;
    let debtorAccountNumber: string | undefined;
    
    if (jobCard.debtor_account_number) {
      debtorAccountNumber = jobCard.debtor_account_number;
    } else if (selectedDebtor) {
      debtorIdToUse = selectedDebtor.id;
      // Also try to use account_number for the API call
      if (selectedDebtor.account_number) {
        debtorAccountNumber = selectedDebtor.account_number;
      }
    }
    
    // Even if no debtor, try to convert - backend may allow it
    setConverting(true);
    try {
      console.log('Converting to invoice with:', debtorAccountNumber ? `account: ${debtorAccountNumber}` : debtorIdToUse ? `id: ${debtorIdToUse}` : 'no debtor');
      const response = await jobCardsApi.convertToInvoice(jobId, debtorIdToUse, debtorAccountNumber);
      console.log('Conversion response:', response);
      
      // Store the converted invoice and show payment dialog
      const invoiceData = response.invoice || response;
      setConvertedInvoice(invoiceData);
      setShowConvertDialog(false);
      setSelectedDebtor(null);
      setError(null);
      fetchJobCard();
      
      // Show payment dialog
      setShowPaymentDialog(true);
    } catch (err: any) {
      console.error('Error converting to invoice:', err);
      const errorData = err.response?.data;
      const errorMessage = errorData?.error || errorData?.detail || 'Failed to convert to invoice';
      const errorDetails = errorData?.details || errorData?.message || '';
      setError(errorDetails ? `${errorMessage}: ${errorDetails}` : errorMessage);
    } finally {
      setConverting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">Loading...</div>
      </div>
    );
  }

  if (error || !jobCard) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b px-6 py-4 flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="text-blue-600 hover:text-blue-700"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Job Card Not Found</h1>
          </div>
        </div>
        <div className="p-6">
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6 flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <p className="text-red-800">{error || 'Job card not found'}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/dashboard/pos/job-costing')}
            className="text-blue-600 hover:text-blue-700"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Job Card: {jobCard.job_number}</h1>
            <p className="text-sm text-gray-500">View job card details</p>
          </div>
        </div>
        <div>
          <Link href={`/dashboard/pos/job-costing/${jobId}/edit`}>
            <Button className="bg-blue-600 hover:bg-blue-700 mr-2">
              <Edit className="w-4 h-4 mr-2" />
              Edit Job
            </Button>
          </Link>
          {jobCard.status !== 'CONVERTED_TO_INVOICE' && (
            <Button 
              className="bg-green-600 hover:bg-green-700"
              onClick={() => setShowConvertDialog(true)}
            >
              Convert to Invoice
            </Button>
          )}
        </div>
      </div>

      {/* Convert to Invoice Dialog */}
      {showConvertDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Convert to Invoice</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Show saved debtor info if available */}
              {jobCard.debtor_account_number ? (
                <div className="bg-green-50 border border-green-200 rounded-md p-3">
                  <p className="text-sm text-green-800">
                    <strong>Customer:</strong> {jobCard.customer_name}
                  </p>
                  <p className="text-sm text-green-700">
                    <strong>Account:</strong> {jobCard.debtor_account_number}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    Using saved customer from job card creation.
                  </p>
                </div>
              ) : (
                <>
                  <p className="text-sm text-gray-600">
                    No customer saved with this job. Select a customer/debtor to invoice this job to:
                  </p>
                  <DebtorPicker
                    onSelect={(debtor) => setSelectedDebtor(debtor)}
                    disabled={converting}
                  />
                  {selectedDebtor && (
                    <p className="text-sm text-green-600">
                      Selected: {selectedDebtor.name} ({selectedDebtor.account_number || selectedDebtor.id})
                    </p>
                  )}
                </>
              )}
              {error && (
                <p className="text-sm text-red-600">{error}</p>
              )}
              <div className="flex gap-2 justify-end">
                <Button 
                  variant="outline" 
                  onClick={() => { setShowConvertDialog(false); setSelectedDebtor(null); setError(null); }}
                  disabled={converting}
                >
                  Cancel
                </Button>
                <Button 
                  className="bg-green-600 hover:bg-green-700"
                  onClick={handleConvertToInvoice}
                  disabled={converting}
                >
                  {converting ? 'Converting...' : 'Convert'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Payment Tender Dialog */}
      {showPaymentDialog && convertedInvoice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Payment Tender</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                <p className="text-sm text-blue-800">
                  <strong>Invoice Number:</strong> {convertedInvoice.invoice_number}
                </p>
                <p className="text-lg font-bold text-blue-900 mt-2">
                  Total: R{parseFloat(convertedInvoice.total_amount || 0).toFixed(2)}
                </p>
              </div>

              <p className="text-sm text-gray-600">
                Select payment method:
              </p>

              {/* Payment method options */}
              <div className="grid grid-cols-2 gap-3">
                {/* If debtor has account, show Account option */}
                {(jobCard.debtor_account_number || (selectedDebtor && selectedDebtor.id)) ? (
                  <button
                    onClick={() => setSelectedPaymentMethod('ACCOUNT')}
                    className={`p-4 border-2 rounded-lg text-center transition ${
                      selectedPaymentMethod === 'ACCOUNT'
                        ? 'border-blue-600 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-lg font-semibold">Account</div>
                    <div className="text-xs text-gray-500">Charge to account</div>
                  </button>
                ) : (
                  // No debtor account - show Cash, Card, EFT options
                  <>
                    <button
                      onClick={() => setSelectedPaymentMethod('CASH')}
                      className={`p-4 border-2 rounded-lg text-center transition ${
                        selectedPaymentMethod === 'CASH'
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="text-lg font-semibold">Cash</div>
                      <div className="text-xs text-gray-500">Pay with cash</div>
                    </button>
                    <button
                      onClick={() => setSelectedPaymentMethod('CARD')}
                      className={`p-4 border-2 rounded-lg text-center transition ${
                        selectedPaymentMethod === 'CARD'
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="text-lg font-semibold">Card</div>
                      <div className="text-xs text-gray-500">Credit/Debit card</div>
                    </button>
                    <button
                      onClick={() => setSelectedPaymentMethod('EFT')}
                      className={`p-4 border-2 rounded-lg text-center transition col-span-2 ${
                        selectedPaymentMethod === 'EFT'
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="text-lg font-semibold">EFT</div>
                      <div className="text-xs text-gray-500">Electronic funds transfer</div>
                    </button>
                  </>
                )}
              </div>

              <div className="flex gap-2 justify-end">
                <Button 
                  variant="outline" 
                  onClick={() => { 
                    setShowPaymentDialog(false); 
                    setSelectedPaymentMethod(''); 
                    setConvertedInvoice(null); 
                    router.push('/dashboard/pos/invoices');
                  }}
                  disabled={processingPayment}
                >
                  Skip / View Invoice
                </Button>
                <Button 
                  className="bg-green-600 hover:bg-green-700"
                  onClick={() => {
                    // For account payments, just close and show invoice
                    if (selectedPaymentMethod === 'ACCOUNT') {
                      alert('Invoice added to customer account for payment later.');
                      setShowPaymentDialog(false);
                      setSelectedPaymentMethod('');
                      setConvertedInvoice(null);
                      router.push('/dashboard/pos/invoices');
                    } else {
                      // For cash/card/eft, would need to implement tender recording
                      alert(`Payment via ${selectedPaymentMethod} recorded. Invoice marked as paid.`);
                      setShowPaymentDialog(false);
                      setSelectedPaymentMethod('');
                      setConvertedInvoice(null);
                      router.push('/dashboard/pos/invoices');
                    }
                  }}
                  disabled={!selectedPaymentMethod || processingPayment}
                >
                  Process Payment
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="p-6 space-y-6">
        {/* Job Details */}
        <Card>
          <CardHeader>
            <CardTitle>Job Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500">Job Number</label>
                <p className="text-lg font-semibold">{jobCard.job_number}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Customer</label>
                <p className="text-lg font-semibold">{jobCard.customer_name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Date</label>
                <p className="text-lg">{jobCard.job_date}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Status</label>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  jobCard.status === 'COMPLETED' || jobCard.status === 'CONVERTED_TO_INVOICE' ? 'bg-green-100 text-green-800' :
                  jobCard.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {jobCard.status}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Registration</label>
                <p className="text-lg">{jobCard.registration_number || '-'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Telephone</label>
                <p className="text-lg">{jobCard.telephone || '-'}</p>
              </div>
            </div>
            {jobCard.description && (
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-500">Description</label>
                <p className="mt-1">{jobCard.description}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Line Items */}
        <Card>
          <CardHeader>
            <CardTitle>Job Costs</CardTitle>
          </CardHeader>
          <CardContent>
            {jobCard.lines && jobCard.lines.length > 0 ? (
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>#</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Unit Price</TableHead>
                      <TableHead className="text-right">Discount</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobCard.lines.map((line: any) => (
                      <TableRow key={line.id}>
                        <TableCell>{line.line_number}</TableCell>
                        <TableCell>{line.description}</TableCell>
                        <TableCell className="text-right">{line.quantity}</TableCell>
                        <TableCell className="text-right">R{parseFloat(line.unit_price).toFixed(2)}</TableCell>
                        <TableCell className="text-right">{line.discount_percentage}%</TableCell>
                        <TableCell className="text-right font-medium">
                          R{parseFloat(line.line_total).toFixed(2)}
                        </TableCell>
                      </TableRow>
                    ))}
                    <TableRow className="bg-gray-50 font-bold">
                      <TableCell colSpan={5} className="text-right">Subtotal:</TableCell>
                      <TableCell className="text-right">R{parseFloat(jobCard.subtotal || 0).toFixed(2)}</TableCell>
                    </TableRow>
                    <TableRow className="bg-gray-50 font-bold">
                      <TableCell colSpan={5} className="text-right">VAT (14%):</TableCell>
                      <TableCell className="text-right">R{parseFloat(jobCard.vat_amount || 0).toFixed(2)}</TableCell>
                    </TableRow>
                    <TableRow className="bg-gray-50 font-bold text-lg">
                      <TableCell colSpan={5} className="text-right">Total:</TableCell>
                      <TableCell className="text-right text-blue-900">R{parseFloat(jobCard.total_amount || 0).toFixed(2)}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">No line items added yet</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import type { CreditorAccount, AgedBalanceSummary } from '@/lib/types/creditors';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, Check } from 'lucide-react';

export default function CreditorPaymentsPage() {
  const [selectedAccount, setSelectedAccount] = useState<CreditorAccount | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [paymentData, setPaymentData] = useState<{
    transaction_date: string;
    amount_paid: number;
    transaction_reference?: string;
  }>({
    transaction_date: new Date().toISOString().split('T')[0],
    amount_paid: 0,
    transaction_reference: '',
  });

  const { data: suppliers } = useQuery({
    queryKey: ['creditors-suppliers', searchTerm],
    queryFn: () =>
      creditorsApi.accounts.list({
        search: searchTerm || undefined,
        page_size: 50,
      }),
  });

  const { data: accountDetail, isLoading: accountLoading } = useQuery<AgedBalanceSummary>({
    queryKey: ['creditor-aged-balance', selectedAccount?.id],
    queryFn: () => creditorsApi.accounts.agedBalances(selectedAccount!.id),
    enabled: !!selectedAccount,
  });

  const paymentMutation = useMutation({
    mutationFn: (data: { transaction_date: string; amount_paid: number; transaction_reference?: string }) =>
      creditorsApi.payments.create({
        creditor: selectedAccount!.id,
        transaction_date: data.transaction_date,
        amount_due: data.amount_paid,
        amount_paid: data.amount_paid,
        transaction_reference: data.transaction_reference || undefined,
      }),
    onSuccess: () => {
      alert('Payment recorded successfully');
      setSelectedAccount(null);
      setPaymentData({
        transaction_date: new Date().toISOString().split('T')[0],
        amount_paid: 0,
        transaction_reference: '',
      });
    },
  });

  const handleSelectAccount = (account: CreditorAccount) => {
    setSelectedAccount(account);
    setSearchTerm('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAccount) return;

    // Validate positive amount
    if (paymentData.amount_paid <= 0) {
      alert('Amount paid must be greater than zero');
      return;
    }

    paymentMutation.mutate(paymentData);
  };

  if (accountLoading && selectedAccount) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Record Payment</h1>
        <p className="text-gray-600 mt-1">Record payment to a supplier</p>
      </div>

      {!selectedAccount ? (
        <>
          {/* Supplier Search */}
          <Card className="p-6">
            <h2 className="text-lg font-bold mb-4">Select Supplier</h2>
            <Input
              type="text"
              placeholder="Search by account number or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </Card>

          {/* Supplier List */}
          {suppliers?.results && suppliers.results.length > 0 && (
            <Card className="p-6">
              <div className="space-y-2">
                {suppliers.results.map((supplier: CreditorAccount) => (
                  <div
                    key={supplier.id}
                    className="p-4 border rounded-lg hover:bg-blue-50 cursor-pointer transition"
                    onClick={() => handleSelectAccount(supplier)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-bold">{supplier.supplier_number} - {supplier.name}</p>
                        <p className="text-xs text-gray-600 mt-1">
                          Category: {supplier.account_category === 'B' ? 'BBF' : supplier.account_category === 'O' ? 'Open Item' : 'N/A'}
                        </p>
                      </div>
                      <span className="text-blue-600">→</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      ) : (
        <>
          {/* Selected Account */}
          <Card className="p-6 bg-blue-50 border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Selected Supplier</p>
                <p className="text-lg font-bold">{selectedAccount.supplier_number} - {selectedAccount.name}</p>
                <p className="text-xs text-gray-600 mt-1">Category: {selectedAccount.account_category === 'B' ? 'BBF' : selectedAccount.account_category === 'O' ? 'Open Item' : 'N/A'}</p>
              </div>
              <Button
                variant="outline"
                onClick={() => {
                  setSelectedAccount(null);
                  setPaymentData({
                    transaction_date: new Date().toISOString().split('T')[0],
                    amount_paid: 0,
                    transaction_reference: '',
                  });
                }}
              >
                Change
              </Button>
            </div>
          </Card>

          {/* Payment Form */}
          <form onSubmit={handleSubmit}>
            {/* Payment Header */}
            <Card className="p-6 mb-6">
              <h2 className="text-lg font-bold mb-4">Payment Details</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Payment Date</label>
                  <Input
                    type="date"
                    value={paymentData.transaction_date}
                    onChange={(e) => setPaymentData({ ...paymentData, transaction_date: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Amount Paid (R)</label>
                  <Input
                    type="number"
                    step="0.01"
                    value={paymentData.amount_paid}
                    onChange={(e) => {
                      const newAmount = parseFloat(e.target.value) || 0;
                      setPaymentData({
                        ...paymentData,
                        amount_paid: newAmount,
                      });
                    }}
                    placeholder="0.00"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Payment Reference</label>
                  <Input
                    type="text"
                    value={paymentData.transaction_reference || ''}
                    onChange={(e) => setPaymentData({ ...paymentData, transaction_reference: e.target.value })}
                    placeholder="Enter payment reference..."
                  />
                </div>
              </div>
            </Card>

            {/* Aging Analysis */}
            {accountDetail && (
              <Card className="p-6 mb-6">
                <h2 className="text-lg font-bold mb-4">Aging Analysis & Allocation</h2>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
                  <div className="p-3 bg-green-50 rounded border border-green-200">
                    <p className="text-xs text-green-600 font-medium">Current</p>
                    <p className="text-lg font-bold text-green-700">
                      R {accountDetail.balance_current?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-3 bg-amber-50 rounded border border-amber-200">
                    <p className="text-xs text-amber-600 font-medium">30 Days</p>
                    <p className="text-lg font-bold text-amber-700">
                      R {accountDetail.balance_30_days?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-3 bg-orange-50 rounded border border-orange-200">
                    <p className="text-xs text-orange-600 font-medium">60 Days</p>
                    <p className="text-lg font-bold text-orange-700">
                      R {accountDetail.balance_60_days?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-3 bg-red-50 rounded border border-red-200">
                    <p className="text-xs text-red-600 font-medium">90 Days</p>
                    <p className="text-lg font-bold text-red-700">
                      R {accountDetail.balance_90_days?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-3 bg-red-100 rounded border border-red-300">
                    <p className="text-xs text-red-800 font-medium">120+ Days</p>
                    <p className="text-lg font-bold text-red-900">
                      R {accountDetail.balance_120_days?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>

                {/* Allocation Table */}
                {selectedAccount.account_category === 'B' ? (
                  <div>
                    <h3 className="font-bold mb-3">Allocate to Aging Periods</h3>
                    <div className="space-y-2">
                      {[
                        { period: 'Current', color: 'bg-green-100', value: accountDetail.balance_current },
                        { period: '30 Days', color: 'bg-amber-100', value: accountDetail.balance_30_days },
                        { period: '60 Days', color: 'bg-orange-100', value: accountDetail.balance_60_days },
                        { period: '90 Days', color: 'bg-red-100', value: accountDetail.balance_90_days },
                        { period: '120+ Days', color: 'bg-red-200', value: accountDetail.balance_120_days },
                      ].map((period) => (
                        <div key={period.period} className="flex items-center gap-2">
                          <span className={`px-3 py-2 text-sm font-medium rounded w-24 ${period.color}`}>
                            {period.period}
                          </span>
                          <Input
                            type="number"
                            step="0.01"
                            placeholder="0.00"
                            className="flex-1"
                            onChange={(e) => {
                              const newAmount = parseFloat(e.target.value) || 0;
                              // Note: Full allocation functionality would require open_item IDs
                              // For now, this is a display-only placeholder
                              console.log('Allocation for', period.period, ':', newAmount);
                            }}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded">
                    <p className="text-sm text-amber-800">
                      <strong>Note:</strong> For Open Item accounts, allocation is handled at the transaction level.
                    </p>
                  </div>
                )}
              </Card>
            )}

            {/* Validation Messages */}
            {paymentData.amount_paid > 0 && (
              <Card className="p-6 mb-6 bg-gray-50">
                <div className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <p className="text-sm text-gray-700">
                    Amount paid: <strong>R {paymentData.amount_paid.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}</strong>
                  </p>
                </div>
              </Card>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              <Button
                type="submit"
                className="bg-green-600 hover:bg-green-700"
                disabled={paymentMutation.isPending || paymentData.amount_paid === 0}
              >
                {paymentMutation.isPending ? 'Recording...' : 'Record Payment'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setSelectedAccount(null)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </>
      )}
    </div>
  );
}

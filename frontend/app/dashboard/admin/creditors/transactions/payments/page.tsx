'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import type { CreditorAccount } from '@/lib/types/creditors';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, Check } from 'lucide-react';

export default function CreditorPaymentsPage() {
  const router = useRouter();
  const [selectedAccount, setSelectedAccount] = useState<CreditorAccount | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [paymentData, setPaymentData] = useState({
    payment_date: new Date().toISOString().split('T')[0],
    amount_tendered: 0,
    allocations: [] as Array<{ aging_period: string; amount: number }>,
  });

  const { data: suppliers } = useQuery({
    queryKey: ['creditors-suppliers', searchTerm],
    queryFn: () =>
      creditorsApi.accounts.list({
        search: searchTerm || undefined,
        page_size: 50,
      }),
  });

  const { data: accountDetail, isLoading: accountLoading } = useQuery({
    queryKey: ['creditor-account-detail', selectedAccount?.id],
    queryFn: () => creditorsApi.accounts.get(selectedAccount!.id),
    enabled: !!selectedAccount,
  });

  const paymentMutation = useMutation({
    mutationFn: (data: any) =>
      creditorsApi.transactions.create({
        ...data,
        account_id: selectedAccount!.id,
        transaction_type: 'PAYMENT',
      }),
    onSuccess: () => {
      alert('Payment recorded successfully');
      setSelectedAccount(null);
      setPaymentData({
        payment_date: new Date().toISOString().split('T')[0],
        amount_tendered: 0,
        allocations: [],
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

    // Validate allocations sum
    const totalAllocated = paymentData.allocations.reduce((sum, a) => sum + a.amount, 0);
    if (totalAllocated !== paymentData.amount_tendered) {
      alert('Allocated amount must match tendered amount');
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
                        <p className="font-bold">{supplier.account_number} - {supplier.name}</p>
                        <p className="text-xs text-gray-600 mt-1">
                          Type: {supplier.account_type} | Balance: R {supplier.balance?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
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
                <p className="text-lg font-bold">{selectedAccount.account_number} - {selectedAccount.name}</p>
                <p className="text-xs text-gray-600 mt-1">Type: {selectedAccount.account_type}</p>
              </div>
              <Button
                variant="outline"
                onClick={() => {
                  setSelectedAccount(null);
                  setPaymentData({
                    payment_date: new Date().toISOString().split('T')[0],
                    amount_tendered: 0,
                    allocations: [],
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
                    value={paymentData.payment_date}
                    onChange={(e) => setPaymentData({ ...paymentData, payment_date: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Amount Tendered (R)</label>
                  <Input
                    type="number"
                    step="0.01"
                    value={paymentData.amount_tendered}
                    onChange={(e) => {
                      const newAmount = parseFloat(e.target.value);
                      setPaymentData({
                        ...paymentData,
                        amount_tendered: newAmount,
                        allocations: [{ aging_period: 'Current', amount: newAmount }],
                      });
                    }}
                    placeholder="0.00"
                    required
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
                      R {accountDetail.current_aging?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-3 bg-amber-50 rounded border border-amber-200">
                    <p className="text-xs text-amber-600 font-medium">30 Days</p>
                    <p className="text-lg font-bold text-amber-700">
                      R {accountDetail.d30?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-3 bg-orange-50 rounded border border-orange-200">
                    <p className="text-xs text-orange-600 font-medium">60 Days</p>
                    <p className="text-lg font-bold text-orange-700">
                      R {accountDetail.d60?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-3 bg-red-50 rounded border border-red-200">
                    <p className="text-xs text-red-600 font-medium">90 Days</p>
                    <p className="text-lg font-bold text-red-700">
                      R {accountDetail.d90?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-3 bg-red-100 rounded border border-red-300">
                    <p className="text-xs text-red-800 font-medium">120+ Days</p>
                    <p className="text-lg font-bold text-red-900">
                      R {accountDetail.d120?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>

                {/* Allocation Table */}
                {selectedAccount.account_type === 'BBF' ? (
                  <div>
                    <h3 className="font-bold mb-3">Allocate to Aging Periods</h3>
                    <div className="space-y-2">
                      {[
                        { period: 'Current', color: 'bg-green-100', value: accountDetail.current_aging },
                        { period: '30 Days', color: 'bg-amber-100', value: accountDetail.d30 },
                        { period: '60 Days', color: 'bg-orange-100', value: accountDetail.d60 },
                        { period: '90 Days', color: 'bg-red-100', value: accountDetail.d90 },
                        { period: '120+ Days', color: 'bg-red-200', value: accountDetail.d120 },
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
                              const newAllocations = paymentData.allocations.filter(
                                (a) => a.aging_period !== period.period
                              );
                              if (e.target.value) {
                                newAllocations.push({
                                  aging_period: period.period,
                                  amount: parseFloat(e.target.value),
                                });
                              }
                              setPaymentData({ ...paymentData, allocations: newAllocations });
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
            {paymentData.amount_tendered > 0 && (
              <Card className="p-6 mb-6 bg-gray-50">
                <div className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <p className="text-sm text-gray-700">
                    Amount tendered: <strong>R {paymentData.amount_tendered.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}</strong>
                  </p>
                </div>
              </Card>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              <Button
                type="submit"
                className="bg-green-600 hover:bg-green-700"
                disabled={paymentMutation.isPending || paymentData.amount_tendered === 0}
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

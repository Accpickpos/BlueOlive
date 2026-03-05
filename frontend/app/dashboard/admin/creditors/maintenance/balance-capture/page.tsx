'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import type { CreditorAccount } from '@/lib/types/creditors';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, Search } from 'lucide-react';

export default function BalanceCapturePageComponent() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAccount, setSelectedAccount] = useState<CreditorAccount | null>(null);
  const [balanceData, setBalanceData] = useState({
    balance_brought_forward: 0,
    effective_date: new Date().toISOString().split('T')[0],
  });

  const { data: accounts, isLoading } = useQuery({
    queryKey: ['creditor-accounts-search', searchTerm],
    queryFn: () =>
      creditorsApi.accounts.list({
        search: searchTerm || undefined,
        page_size: 50,
      }),
  });

  const updateMutation = useMutation({
    mutationFn: (data: any) =>
      creditorsApi.outstandingBalances.update(selectedAccount!.id, data),
    onSuccess: () => {
      setSelectedAccount(null);
      setBalanceData({ balance_brought_forward: 0, effective_date: new Date().toISOString().split('T')[0] });
      alert('Balance updated successfully');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAccount) return;
    updateMutation.mutate(balanceData);
  };

  if (isLoading && !selectedAccount) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Balance Capture</h1>
        <p className="text-gray-600 mt-1">Record opening balances for BBF (Balance Brought Forward) or Open Item accounts</p>
      </div>

      {!selectedAccount ? (
        <>
          {/* Search */}
          <Card className="p-6">
            <h2 className="text-lg font-bold mb-4">Select Account</h2>
            <div className="relative">
              <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search by account number or name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </Card>

          {/* Account List */}
          <Card className="p-6">
            <div className="space-y-2">
              {accounts?.results?.map((account: CreditorAccount) => (
                <div
                  key={account.id}
                  className="p-4 border rounded hover:bg-blue-50 cursor-pointer transition"
                  onClick={() => setSelectedAccount(account)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{account.supplier_number} - {account.name}</p>
                      <p className="text-xs text-gray-600">
                        Type: {account.account_category === 'B' ? 'BBF' : account.account_category === 'O' ? 'Open Item' : 'Unknown'} | Current Balance: R {account.total_outstanding_balance?.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                      </p>
                    </div>
                    <span className="text-blue-600">→</span>
                  </div>
                </div>
              ))}
            </div>
            {(!accounts?.results || accounts.results.length === 0) && (
              <p className="text-center text-gray-500 py-8">No accounts found. Try a different search term.</p>
            )}
          </Card>
        </>
      ) : (
        <>
          {/* Selected Account */}
          <Card className="p-6 bg-blue-50 border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Selected Account</p>
                <p className="text-lg font-bold">{selectedAccount.supplier_number} - {selectedAccount.name}</p>
                <p className="text-xs text-gray-600 mt-1">Type: {selectedAccount.account_category === 'B' ? 'BBF' : selectedAccount.account_category === 'O' ? 'Open Item' : 'Unknown'}</p>
              </div>
              <Button
                variant="outline"
                onClick={() => setSelectedAccount(null)}
              >
                Change
              </Button>
            </div>
          </Card>

          {/* Balance Form */}
          <form onSubmit={handleSubmit}>
            <Card className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Effective Date</label>
                <Input
                  type="date"
                  value={balanceData.effective_date}
                  onChange={(e) => setBalanceData({ ...balanceData, effective_date: e.target.value })}
                  required
                />
                <p className="text-xs text-gray-600 mt-1">Date when this balance becomes effective</p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Balance Brought Forward (R)</label>
                <Input
                  type="number"
                  step="0.01"
                  value={balanceData.balance_brought_forward}
                  onChange={(e) =>
                    setBalanceData({
                      ...balanceData,
                      balance_brought_forward: parseFloat(e.target.value),
                    })
                  }
                  placeholder="0.00"
                  required
                />
                <p className="text-xs text-gray-600 mt-1">The opening balance as at the effective date</p>
              </div>

              {selectedAccount.account_category === 'O' && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded">
                  <p className="text-sm text-amber-800">
                    <strong>Note:</strong> For Open Item accounts, you may also need to record individual open items in the Transactions section.
                  </p>
                </div>
              )}
            </Card>

            {/* Actions */}
            <div className="flex gap-2 mt-6">
              <Button
                type="submit"
                className="bg-green-600 hover:bg-green-700"
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? 'Saving...' : 'Save Balance'}
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

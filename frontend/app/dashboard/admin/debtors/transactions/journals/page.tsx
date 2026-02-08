'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import TransactionForm from '@/components/debtors/forms/TransactionForm';
import TransactionHistory from '@/components/debtors/transactions/TransactionHistory';
import { TransactionType, type Transaction } from '@/lib/types/debtors';

export default function JournalsPage() {
  const [activeType, setActiveType] = useState<TransactionType>(TransactionType.INVOICE);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const { data: transactions } = useQuery({
    queryKey: ['transactions', activeType, refreshTrigger],
    queryFn: () =>
      debtorsApi.transactions.list({
        transaction_type: activeType,
      }),
    staleTime: 2 * 60 * 1000,
  });

  const transactionTypes = [
    { value: TransactionType.INVOICE, label: 'Invoices', color: 'bg-blue-500' },
    { value: TransactionType.CREDITNOTE, label: 'Credit Notes', color: 'bg-green-500' },
    { value: TransactionType.JOURNALDEBIT, label: 'Journal Debits', color: 'bg-orange-500' },
    { value: TransactionType.JOURNALCREDIT, label: 'Journal Credits', color: 'bg-purple-500' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Journal Entries</h1>
        <p className="text-gray-600 mt-1">Post debit and credit journal entries for debtors</p>
      </div>

      {/* Post New Journal */}
      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Post New Journal Entry</h2>
        <TransactionForm
          onSuccess={() => setRefreshTrigger((prev) => prev + 1)}
        />
      </Card>

      {/* Journal History by Type */}
      <div>
        <h2 className="text-lg font-bold mb-4">Journal History</h2>
        <Tabs defaultValue={TransactionType.INVOICE}>
          <TabsList className="grid w-full grid-cols-4 mb-6">
            {transactionTypes.map((type) => (
              <TabsTrigger key={type.value} value={type.value}>
                {type.label}
              </TabsTrigger>
            ))}
          </TabsList>

          {transactionTypes.map((type) => (
            <TabsContent key={type.value} value={type.value}>
              <TransactionHistory
                type={type.value}
                transactions={transactions?.results || []}
              />
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
}

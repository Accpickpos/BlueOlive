'use client';

import type { Transaction, TransactionType } from '@/lib/types/debtors';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface TransactionHistoryProps {
  type: TransactionType;
  transactions: Transaction[];
}

const TYPE_LABELS: Record<TransactionType, { label: string; color: string }> = {
  IN: { label: 'Invoice', color: 'bg-blue-100 text-blue-800' },
  CN: { label: 'Credit Note', color: 'bg-green-100 text-green-800' },
  CS: { label: 'Cash Sale', color: 'bg-purple-100 text-purple-800' },
  CR: { label: 'Correction', color: 'bg-orange-100 text-orange-800' },
  RCP: { label: 'Receipt', color: 'bg-emerald-100 text-emerald-800' },
  INT: { label: 'Interest', color: 'bg-red-100 text-red-800' },
  JD: { label: 'J. Debit', color: 'bg-yellow-100 text-yellow-800' },
  JC: { label: 'J. Credit', color: 'bg-gray-100 text-gray-800' },
};

export default function TransactionHistory({ type, transactions }: TransactionHistoryProps) {
  const filtered = transactions.filter((t) => t.transaction_type === type);

  return (
    <Card className="p-4">
      {filtered.length === 0 ? (
        <div className="text-center py-8 text-gray-600">No transactions found</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Date</th>
                <th className="px-4 py-3 text-left font-semibold">Debtor</th>
                <th className="px-4 py-3 text-left font-semibold">Reference</th>
                <th className="px-4 py-3 text-left font-semibold">Description</th>
                <th className="px-4 py-3 text-right font-semibold">Amount</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((transaction) => (
                <tr key={transaction.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3">{new Date(transaction.transaction_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3">{transaction.debtor_name || `ID: ${transaction.debtor_id}`}</td>
                  <td className="px-4 py-3">{transaction.reference_number || '-'}</td>
                  <td className="px-4 py-3 text-gray-600">{transaction.description || '-'}</td>
                  <td className="px-4 py-3 text-right font-semibold">${transaction.amount?.toLocaleString('en-US', { maximumFractionDigits: 2 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

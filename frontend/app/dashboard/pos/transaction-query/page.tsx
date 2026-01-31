// app/pos/transaction-query/page.tsx
"use client";
import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";

const transactionsData = [
  { id: "TX-001", type: "Cash Sale", date: "2025-09-01", amount: "$450" },
  { id: "TX-002", type: "Invoice", date: "2025-09-02", amount: "$1,200" },
  { id: "TX-003", type: "Cash Sale", date: "2025-09-02", amount: "$300" },
  { id: "TX-004", type: "Invoice", date: "2025-08-28", amount: "$2,400" },
];

export default function TransactionQuery() {
  const [transactions, setTransactions] = useState(transactionsData);
  const [searchDate, setSearchDate] = useState("");

  const filteredTransactions = searchDate
    ? transactions.filter((tx) => tx.date === searchDate)
    : transactions;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Transaction Query</h1>

      {/* Date Filter */}
      <div className="flex gap-4 items-center">
        <label className="text-gray-600">Search by Date:</label>
        <input
          type="date"
          value={searchDate}
          onChange={(e) => setSearchDate(e.target.value)}
          className="border p-2 rounded-lg"
        />
        <button
          onClick={() => setSearchDate("")}
          className="px-4 py-2 rounded-lg bg-gray-200 hover:bg-gray-300"
        >
          Clear
        </button>
      </div>

      {/* Transaction Table */}
      <Card>
        <CardContent className="p-6">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100 text-left">
                <th className="p-3 border-b">ID</th>
                <th className="p-3 border-b">Type</th>
                <th className="p-3 border-b">Date</th>
                <th className="p-3 border-b">Amount</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.map((tx) => (
                <tr key={tx.id} className="hover:bg-gray-50">
                  <td className="p-3 border-b">{tx.id}</td>
                  <td className="p-3 border-b">{tx.type}</td>
                  <td className="p-3 border-b">{tx.date}</td>
                  <td className="p-3 border-b">{tx.amount}</td>
                </tr>
              ))}
              {filteredTransactions.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-center p-4 text-gray-500">
                    No transactions found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

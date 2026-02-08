"use client";

import { useState } from "react";

// Fake sample data
const accounts = [
  { number: "10000", name: "ABC Supplies", searchName: "ABC", balance: 1200.5, email: "abc@supplies.com" },
  { number: "10001", name: "XYZ Traders", searchName: "XYZ", balance: 850.0, email: "contact@xyz.com" },
  { number: "10002", name: "John Doe", searchName: "DOE", balance: -50.25, email: "john@doe.com" },
  { number: "10003", name: "Acme Corp", searchName: "ACME", balance: 3000.0, email: "accounts@acme.com" },
];

interface DebtorBalanceModalProps {
  open: boolean;
  onClose: () => void;
}

export default function DebtorBalanceModal({ open, onClose }: DebtorBalanceModalProps) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<any | null>(null);

  if (!open) return null;

  const filtered = accounts.filter(
    (acc) =>
      acc.number.includes(query) ||
      acc.name.toLowerCase().includes(query.toLowerCase()) ||
      acc.searchName.toLowerCase().includes(query.toLowerCase())
  );

  const handlePrint = (account: any) => {
    alert(`Printing statement for ${account.name}`); // Replace with PDF export
  };

  const handleEmail = (account: any) => {
    alert(`Email sent to ${account.email}`); // Replace with API integration
  };

  return (
    <>
      {/* Full page Account Balance Modal */}
      <div className="fixed inset-0 flex flex-col bg-white z-50">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b shadow">
          <h2 className="text-2xl font-bold">Account Balances</h2>
          <button onClick={onClose} className="px-4 py-2 border rounded">
            Close
          </button>
        </div>

        {/* Search bar */}
        <div className="p-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by Account Number, Name, or Search Name"
            className="w-full border p-2 rounded"
          />
        </div>

        {/* Table */}
        <div className="flex-1 overflow-y-auto p-4">
          <table className="w-full border-collapse border text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-3 py-2 text-left">Account #</th>
                <th className="border px-3 py-2 text-left">Name</th>
                <th className="border px-3 py-2 text-left">Balance</th>
                <th className="border px-3 py-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((acc) => (
                <tr key={acc.number} className="hover:bg-gray-50">
                  <td className="border px-3 py-2">{acc.number}</td>
                  <td className="border px-3 py-2">{acc.name}</td>
                  <td
                    className={`border px-3 py-2 text-right ${
                      acc.balance < 0 ? "text-red-600" : "text-green-600"
                    }`}
                  >
                    {acc.balance.toFixed(2)}
                  </td>
                  <td className="border px-3 py-2 text-center">
                    <button
                      onClick={() => setSelected(acc)}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-center py-4 text-gray-500">
                    No accounts found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Full page Account Detail Modal */}
      {selected && (
        <div className="fixed inset-0 flex flex-col bg-white z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b shadow">
            <h3 className="text-2xl font-bold">Account Details</h3>
            <button
              onClick={() => setSelected(null)}
              className="px-4 py-2 border rounded"
            >
              Back
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-3">
            <p><strong>Account #:</strong> {selected.number}</p>
            <p><strong>Name:</strong> {selected.name}</p>
            <p><strong>Search Name:</strong> {selected.searchName}</p>
            <p><strong>Email:</strong> {selected.email}</p>
            <p className={`mt-2 font-semibold ${selected.balance < 0 ? "text-red-600" : "text-green-600"}`}>
              Balance: {selected.balance.toFixed(2)}
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 p-4 border-t">
            <button
              onClick={() => handlePrint(selected)}
              className="px-4 py-2 bg-gray-700 text-white rounded"
            >
              Print
            </button>
            <button
              onClick={() => handleEmail(selected)}
              className="px-4 py-2 bg-green-600 text-white rounded"
            >
              Email
            </button>
          </div>
        </div>
      )}
    </>
  );
}

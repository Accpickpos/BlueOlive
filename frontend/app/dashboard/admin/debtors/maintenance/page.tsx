"use client";

import { useState } from "react";
import DebtorAccountForm from "@/components/DebtorAccountForm";
import DebtorBalanceModal from "@/components/DebtorBalanceModal";

export default function DebtorsMaintenancePage() {
  const [showAccountForm, setShowAccountForm] = useState(false);
  const [showBalance, setShowBalance] = useState(false);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Debtors - Maintenance</h1>
      <p className="text-gray-600">Choose what you want to manage.</p>

      <div className="flex gap-4">
        <button
          onClick={() => setShowAccountForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded shadow"
        >
          Account Details
        </button>
        <button
          onClick={() => setShowBalance(true)}
          className="px-4 py-2 bg-purple-600 text-white rounded shadow"
        >
          Account Balance
        </button>
      </div>

      {/* Account Form Modal */}
      <DebtorAccountForm open={showAccountForm} onClose={() => setShowAccountForm(false)} />

      {/* Balance Modal */}
      <DebtorBalanceModal open={showBalance} onClose={() => setShowBalance(false)} />
    </div>
  );
}

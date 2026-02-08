'use client';

import DebtorsList from '@/components/DebtorsList';
import { useState } from 'react';

export default function DebtorsMaintenancePage() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Debtors - Maintenance</h1>
        <p className="text-gray-600">Create, update, and manage debtor records.</p>
      </div>
      <DebtorsList onRefresh={refreshTrigger} />
    </div>
  );
}

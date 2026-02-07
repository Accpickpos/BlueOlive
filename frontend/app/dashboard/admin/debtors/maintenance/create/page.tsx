'use client';

import { useRouter } from 'next/navigation';
import DebtorForm from '@/components/DebtorForm';

export default function CreateDebtorPage() {
  const router = useRouter();

  const handleSuccess = () => {
    router.push('/dashboard/admin/debtors/maintenance');
  };

  const handleCancel = () => {
    router.back();
  };

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Create New Debtor</h1>
        <p className="text-gray-600">Add a new customer/debtor account to the system.</p>
      </div>
      <DebtorForm onSuccess={handleSuccess} onCancel={handleCancel} />
    </div>
  );
}

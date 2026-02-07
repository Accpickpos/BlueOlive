'use client';

import { useRouter, useParams } from 'next/navigation';
import DebtorForm from '@/components/DebtorForm';

export default function EditDebtorPage() {
  const router = useRouter();
  const params = useParams();
  const debtorId = params.id ? parseInt(params.id as string) : undefined;

  const handleSuccess = () => {
    router.push('/dashboard/admin/debtors/maintenance');
  };

  const handleCancel = () => {
    router.back();
  };

  if (!debtorId) {
    return <div className="p-6">Invalid debtor ID</div>;
  }

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Edit Debtor</h1>
        <p className="text-gray-600">Update customer/debtor account information.</p>
      </div>
      <DebtorForm debtorId={debtorId} onSuccess={handleSuccess} onCancel={handleCancel} />
    </div>
  );
}

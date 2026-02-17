'use client';

import { useRouter, useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import DebtorAccountForm from '@/components/debtors/forms/DebtorAccountForm';
import debtorsApi from '@/lib/debtorsApi';
import { Loader, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function EditDebtorPage() {
  const router = useRouter();
  const params = useParams();
  const debtorId = params.id ? parseInt(params.id as string) : undefined;

  const { data: debtor, isLoading, error } = useQuery({
    queryKey: ['debtor', debtorId],
    queryFn: () => debtorsApi.accounts.get(debtorId!),
    enabled: !!debtorId,
  });

  const handleSuccess = () => {
    router.push('/dashboard/admin/debtors/maintenance');
  };

  if (!debtorId) {
    return <div className="p-6">Invalid debtor ID</div>;
  }

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <Loader className="animate-spin" />
      </div>
    );
  }

  if (error) {
    return <div className="p-6 text-red-600">Failed to load debtor information</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => router.back()} size="sm">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Edit Debtor</h1>
          <p className="text-gray-600 mt-1">Update customer/debtor account information.</p>
        </div>
      </div>
      <DebtorAccountForm
        initialData={debtor}
        isEdit={true}
        onSuccess={handleSuccess}
      />
    </div>
  );
}

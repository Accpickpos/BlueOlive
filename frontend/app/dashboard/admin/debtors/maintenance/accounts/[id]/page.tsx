'use client';

import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import DebtorAccountForm from '@/components/debtors/forms/DebtorAccountForm';
import { ArrowLeft, Loader } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EditAccountPageProps {
  params: {
    id: string;
  };
}

export default function EditAccountPage({ params }: EditAccountPageProps) {
  const router = useRouter();
  const accountId = parseInt(params.id);

  const { data: account, isLoading } = useQuery({
    queryKey: ['debtor-account', accountId],
    queryFn: () => debtorsApi.accounts.get(accountId),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => router.back()} size="sm">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Edit Account</h1>
          <p className="text-gray-600 mt-1">{account?.dname}</p>
        </div>
      </div>

      <Card className="p-6">
        {account ? (
          <DebtorAccountForm initialData={account} isEdit onSuccess={() => router.push('/dashboard/admin/debtors/maintenance/accounts')} />
        ) : (
          <div className="text-center text-gray-600 py-8">Account not found</div>
        )}
      </Card>
    </div>
  );
}

'use client';

import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import DebtorAccountForm from '@/components/debtors/forms/DebtorAccountForm';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function NewAccountPage() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => router.back()} size="sm">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Create New Account</h1>
          <p className="text-gray-600 mt-1">Add a new debtor account to the system</p>
        </div>
      </div>

      <Card className="p-6">
        <DebtorAccountForm onSuccess={() => router.push('/dashboard/admin/debtors/maintenance/accounts')} />
      </Card>
    </div>
  );
}

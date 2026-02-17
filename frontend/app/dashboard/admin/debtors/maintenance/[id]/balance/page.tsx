'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiRequest } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

interface DebtorInfo {
  id: number;
  account_number: string;
  name: string;
  account_category: string;
  contact_person: string;
  telephone1: string;
  email: string;
  credit_limit: number;
  current_balance: number;
  is_active: boolean;
  is_blocked: boolean;
}

export default function DebtorBalancePage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const [debtorId, setDebtorId] = useState<string | null>(null);
  const [debtor, setDebtor] = useState<DebtorInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    params.then((p) => {
      setDebtorId(p.id);
    });
  }, [params]);

  useEffect(() => {
    if (debtorId) {
      fetchDebtor();
    }
  }, [debtorId]);

  const fetchDebtor = async () => {
    try {
      setLoading(true);
      const response = await apiRequest(`/api/debtors/${debtorId}/`);
      setDebtor(response.data || response);
    } catch (err: any) {
      console.error('Failed to load debtor:', err);
      setError('Failed to load debtor information');
    } finally {
      setLoading(false);
    }
  };

  const getAccountCategoryLabel = (category: string) => {
    const labels: { [key: string]: string } = {
      '': 'Balance Brought Forward',
      'O': 'Open Item',
      'C': 'Cash Customer',
    };
    return labels[category] || category;
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center py-8">Loading debtor information...</div>
      </div>
    );
  }

  if (error || !debtor) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error || 'Debtor not found'}
        </div>
        <div className="mt-4">
          <Link
            href="/dashboard/admin/debtors/maintenance"
            className="text-blue-600 hover:text-blue-800"
          >
            ← Back to Debtors
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={() => router.back()} size="sm">
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{debtor.name}</h1>
            <p className="text-gray-600 mt-1">Account #{debtor.account_number}</p>
          </div>
        </div>
      </div>

      {/* Debtor Info Card */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Debtor Information</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Contact Person</p>
              <p className="text-gray-900 font-medium">{debtor.contact_person || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Telephone</p>
              <p className="text-gray-900 font-medium">{debtor.telephone1 || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Email</p>
              <p className="text-gray-900 font-medium">{debtor.email || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Account Category</p>
              <p className="text-gray-900 font-medium">
                {getAccountCategoryLabel(debtor.account_category)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Credit Limit</p>
              <p className="text-gray-900 font-medium">
                R {parseFloat(String(debtor.credit_limit)).toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Current Balance</p>
              <p className={`text-lg font-bold ${debtor.current_balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                R {parseFloat(String(debtor.current_balance)).toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <p className="text-gray-900 font-medium">
                {debtor.is_blocked ? (
                  <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
                    Blocked
                  </span>
                ) : debtor.is_active ? (
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                    Active
                  </span>
                ) : (
                  <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                    Inactive
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

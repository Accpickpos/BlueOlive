'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import DebtorDetailCard from '@/components/debtors/enquiries/DebtorDetailCard';
import AgeAnalysisDisplay from '@/components/debtors/enquiries/AgeAnalysisDisplay';
import { Search, AlertCircle } from 'lucide-react';

export default function AccountEnquiryPage() {
  const [debtorId, setDebtorId] = useState<number | null>(null);
  const [searchInput, setSearchInput] = useState('');

  const { data: debtor, isLoading, error } = useQuery({
    queryKey: ['debtor-detail', debtorId],
    queryFn: () => debtorsApi.accounts.get(debtorId!),
    enabled: !!debtorId,
    staleTime: 3 * 60 * 1000,
  });

  const { data: ageAnalysis } = useQuery({
    queryKey: ['debtor-age-analysis', debtorId],
    queryFn: () => debtorsApi.accounts.getAgeAnalysis(debtorId!),
    enabled: !!debtorId,
  });

  const handleSearch = async () => {
    const id = parseInt(searchInput);
    if (id) {
      setDebtorId(id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Account Enquiry</h1>
        <p className="text-gray-600 mt-1">View detailed account information and aging analysis</p>
      </div>

      {/* Search */}
      <Card className="p-4">
        <div className="flex gap-2">
          <Input
            type="number"
            placeholder="Enter debtor ID..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button onClick={handleSearch} className="bg-blue-600 hover:bg-blue-700">
            <Search className="w-4 h-4" />
          </Button>
        </div>
      </Card>

      {/* Results */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800">Failed to load account details</div>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-8 text-gray-600">Loading account details...</div>
      ) : debtor ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Account Details */}
          <div className="lg:col-span-2">
            <DebtorDetailCard debtor={debtor} />
          </div>

          {/* Age Analysis */}
          <div className="lg:col-span-1">
            {ageAnalysis && <AgeAnalysisDisplay ageAnalysis={ageAnalysis} />}
          </div>
        </div>
      ) : debtorId ? (
        <Card className="p-4 text-center text-gray-600">Account not found</Card>
      ) : (
        <Card className="p-8 text-center text-gray-600">
          Enter a debtor ID to view account details
        </Card>
      )}
    </div>
  );
}

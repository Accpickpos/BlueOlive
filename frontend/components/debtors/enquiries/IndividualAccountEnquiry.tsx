'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Search, Loader, ChevronDown, ChevronUp } from 'lucide-react';
import type { DebtorAccount, OpenItem, AgeAnalysis } from '@/lib/types/debtors';

export default function IndividualAccountEnquiry() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDebtor, setSelectedDebtor] = useState<DebtorAccount | null>(null);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [showOpenItems, setShowOpenItems] = useState(true);
  const [showAgeAnalysis, setShowAgeAnalysis] = useState(true);

  // Search debtors
  const { data: searchResults, isLoading: isSearching } = useQuery({
    queryKey: ['debtors-search', searchTerm],
    queryFn: () => debtorsApi.accounts.list({ search: searchTerm, page_size: 10 }),
    enabled: searchTerm.length >= 2,
  });

  // Get debtor details
  const { data: debtorDetails, isLoading: isLoadingDetails } = useQuery({
    queryKey: ['debtor-detail', selectedDebtor?.id],
    queryFn: () => debtorsApi.accounts.get(selectedDebtor!.id),
    enabled: !!selectedDebtor,
  });

  // Get open items
  const { data: openItemsData, isLoading: isLoadingOpenItems } = useQuery({
    queryKey: ['debtor-open-items', selectedDebtor?.id],
    queryFn: () => debtorsApi.openItems.list(selectedDebtor!.id),
    enabled: !!selectedDebtor,
  });

  // Get age analysis
  const { data: ageAnalysisData, isLoading: isLoadingAgeAnalysis } = useQuery({
    queryKey: ['debtor-age-analysis', selectedDebtor?.id],
    queryFn: () => debtorsApi.accounts.getAgeAnalysis(selectedDebtor!.id),
    enabled: !!selectedDebtor,
  });

  const handleSelectDebtor = (debtor: DebtorAccount) => {
    setSelectedDebtor(debtor);
    setSearchTerm(debtor.name);
    setShowSearchResults(false);
  };

  const debtors = searchResults?.results || [];

  return (
    <div className="space-y-6">
      {/* Search Section */}
      <div className="relative">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Search for Debtor Account
        </label>
        <div className="relative">
          <Input
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setShowSearchResults(true);
              if (!e.target.value) {
                setSelectedDebtor(null);
              }
            }}
            onFocus={() => setShowSearchResults(true)}
            placeholder="Enter debtor name or account number..."
            className="w-full pr-10"
          />
          <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        </div>

        {/* Search Results Dropdown */}
        {showSearchResults && searchTerm.length >= 2 && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-64 overflow-y-auto">
            {isSearching ? (
              <div className="p-4 text-center text-gray-500">
                <Loader className="w-5 h-5 mx-auto animate-spin" />
                <span className="text-sm">Searching...</span>
              </div>
            ) : debtors.length > 0 ? (
              debtors.map((debtor: DebtorAccount) => (
                <button
                  key={debtor.id}
                  onClick={() => handleSelectDebtor(debtor)}
                  className="w-full text-left px-4 py-3 hover:bg-blue-50 border-b border-gray-100 last:border-b-0 transition-colors"
                >
                  <div className="font-medium text-gray-900">{debtor.name}</div>
                  <div className="text-sm text-gray-600">
                    Account: {debtor.customer_number} | Balance: R{debtor.total_balance?.toFixed(2) || '0.00'}
                  </div>
                </button>
              ))
            ) : (
              <div className="p-4 text-center text-gray-500 text-sm">
                No debtors found
              </div>
            )}
          </div>
        )}
      </div>

      {/* Selected Debtor Details */}
      {selectedDebtor && (
        <>
          {/* Balance Brought Forward Section */}
          <Card className="p-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Balance Brought Forward</h3>
            
            {isLoadingDetails ? (
              <div className="text-center py-4">
                <Loader className="w-5 h-5 mx-auto animate-spin text-gray-400" />
              </div>
            ) : debtorDetails ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">Account Number</p>
                  <p className="font-semibold text-gray-900">{debtorDetails.customer_number}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">Total Balance</p>
                  <p className="font-semibold text-gray-900">R{debtorDetails.total_balance?.toFixed(2) || '0.00'}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">Credit Limit</p>
                  <p className="font-semibold text-gray-900">R{debtorDetails.credit_limit?.toFixed(2) || '0.00'}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">Status</p>
                  <p className={`font-semibold ${debtorDetails.is_active ? 'text-green-600' : 'text-red-600'}`}>
                    {debtorDetails.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                No details available
              </div>
            )}
          </Card>

          {/* Open Items Section */}
          <Card className="p-4">
            <button
              onClick={() => setShowOpenItems(!showOpenItems)}
              className="w-full flex items-center justify-between mb-4"
            >
              <h3 className="text-lg font-bold text-gray-900">Open Items</h3>
              {showOpenItems ? (
                <ChevronUp className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              )}
            </button>

            {showOpenItems && (
              <>
                {isLoadingOpenItems ? (
                  <div className="text-center py-4">
                    <Loader className="w-5 h-5 mx-auto animate-spin text-gray-400" />
                  </div>
                ) : openItemsData?.results && openItemsData.results.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="border-b bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left font-semibold text-gray-700">Document</th>
                          <th className="px-4 py-3 text-left font-semibold text-gray-700">Date</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">Type</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">Amount</th>
                          <th className="px-4 py-3 text-right font-semibold text-gray-700">Outstanding</th>
                        </tr>
                      </thead>
                      <tbody>
                        {openItemsData.results.map((item: OpenItem) => (
                          <tr key={item.id} className="border-b hover:bg-gray-50">
                            <td className="px-4 py-3">{item.document_number || `DOC-${item.id}`}</td>
                            <td className="px-4 py-3">
                              {item.document_date ? new Date(item.document_date).toLocaleDateString() : '-'}
                            </td>
                            <td className="px-4 py-3 text-right capitalize">{item.document_type?.replace('_', ' ') || '-'}</td>
                            <td className="px-4 py-3 text-right">R{item.amount?.toFixed(2) || '0.00'}</td>
                            <td className="px-4 py-3 text-right font-semibold">R{item.outstanding?.toFixed(2) || '0.00'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    No open items for this debtor
                  </div>
                )}
              </>
            )}
          </Card>

          {/* Age Analysis Section */}
          <Card className="p-4">
            <button
              onClick={() => setShowAgeAnalysis(!showAgeAnalysis)}
              className="w-full flex items-center justify-between mb-4"
            >
              <h3 className="text-lg font-bold text-gray-900">Age Analysis</h3>
              {showAgeAnalysis ? (
                <ChevronUp className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              )}
            </button>

            {showAgeAnalysis && (
              <>
                {isLoadingAgeAnalysis ? (
                  <div className="text-center py-4">
                    <Loader className="w-5 h-5 mx-auto animate-spin text-gray-400" />
                  </div>
                ) : ageAnalysisData ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                      {ageAnalysisData.buckets?.map((bucket: any, idx: number) => (
                        <div key={idx} className="bg-gray-50 p-3 rounded-lg">
                          <p className="text-xs text-gray-600 mb-1">{bucket.label}</p>
                          <p className="font-semibold text-gray-900">R{bucket.amount?.toFixed(2) || '0.00'}</p>
                        </div>
                      ))}
                    </div>
                    <div className="border-t pt-4">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-gray-700">Total Outstanding</span>
                        <span className="text-xl font-bold text-blue-600">
                          R{ageAnalysisData.total_balance?.toFixed(2) || '0.00'}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    No age analysis available
                  </div>
                )}
              </>
            )}
          </Card>
        </>
      )}

      {/* Empty State */}
      {!selectedDebtor && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Search className="w-12 h-12 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Search for a debtor account above to view their details</p>
        </div>
      )}
    </div>
  );
}

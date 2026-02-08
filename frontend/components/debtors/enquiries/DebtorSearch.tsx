'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

interface Debtor {
  id: number;
  name: string;
  account_number: string;
  account_category: string;
  current_balance: number;
}

interface DebtorSearchProps {
  onSelect: (debtor: Debtor) => void;
}

export default function DebtorSearch({ onSelect }: DebtorSearchProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [debtors, setDebtors] = useState<Debtor[]>([]);
  const [filteredDebtors, setFilteredDebtors] = useState<Debtor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    loadDebtors();
  }, []);

  useEffect(() => {
    if (searchTerm.trim()) {
      const filtered = debtors.filter(debtor =>
        debtor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        debtor.account_number.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredDebtors(filtered);
      setShowDropdown(true);
    } else {
      setFilteredDebtors([]);
      setShowDropdown(false);
    }
  }, [searchTerm, debtors]);

  const loadDebtors = async () => {
    try {
      const response = await apiRequest('/api/debtors/');
      if ((response as any).results) {
        setDebtors((response as any).results);
      } else if (Array.isArray(response)) {
        setDebtors(response);
      }
    } catch (err) {
      setError('Failed to load debtors');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDebtor = (debtor: Debtor) => {
    onSelect(debtor);
    setSearchTerm('');
    setShowDropdown(false);
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Select Debtor Account</h2>
        
        <div className="relative">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Enter Account Number or Debtor Name
          </label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onFocus={() => searchTerm && setShowDropdown(true)}
            placeholder="Search by account number or name..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />

          {/* Dropdown Results */}
          {showDropdown && filteredDebtors.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-96 overflow-y-auto">
              {filteredDebtors.map(debtor => (
                <button
                  key={debtor.id}
                  onClick={() => handleSelectDebtor(debtor)}
                  className="w-full text-left px-4 py-3 hover:bg-blue-50 border-b border-gray-100 last:border-b-0 transition-colors"
                >
                  <div className="font-medium text-gray-900">{debtor.name}</div>
                  <div className="text-sm text-gray-600">
                    Account: {debtor.account_number} | Balance: R{debtor.current_balance.toFixed(2)}
                  </div>
                </button>
              ))}
            </div>
          )}

          {showDropdown && searchTerm && filteredDebtors.length === 0 && !loading && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg p-4 text-center text-gray-600">
              No debtors found matching "{searchTerm}"
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {!searchTerm && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-3">Recent Debtors</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {debtors.slice(0, 6).map(debtor => (
              <button
                key={debtor.id}
                onClick={() => handleSelectDebtor(debtor)}
                className="text-left p-3 rounded-lg bg-white hover:bg-blue-100 border border-blue-100 hover:border-blue-300 transition-colors"
              >
                <div className="font-medium text-sm text-gray-900">{debtor.name}</div>
                <div className="text-xs text-gray-600">{debtor.account_number}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

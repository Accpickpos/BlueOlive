'use client';

import { useState, useEffect } from 'react';
import { useDebtorsAPI } from '@/lib/debtorsApi';
import DebtorSearch from './DebtorSearch';
import AccountBalance from './AccountBalance';
import SalesAnalysis from './SalesAnalysis';
import TransactionHistory from './TransactionHistory';

interface Debtor {
  id: number;
  name: string;
  account_number: string;
  account_category: string;
  current_balance: number;
}

interface BalanceDetails {
  opening_balance: number;
  current_balance: number;
  age_current: number;
  age_30: number;
  age_60: number;
  age_90: number;
  age_120: number;
  age_150: number;
  age_180: number;
}

export default function IndividualAccountEnquiry() {
  const [selectedDebtor, setSelectedDebtor] = useState<Debtor | null>(null);
  const [balanceDetails, setBalanceDetails] = useState<BalanceDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [viewFormat, setViewFormat] = useState<'details' | 'layout'>('details');
  const [orderNumber, setOrderNumber] = useState('');
  const [vatNumber, setVatNumber] = useState('');

  const loadBalanceDetails = async (debtorId: number) => {
    setLoading(true);
    setError('');
    try {
      const api = useDebtorsAPI();
      const response = await api.getDebtorBalanceDetails(debtorId);
      setBalanceDetails(response as any);
    } catch (err: any) {
      setError('Failed to load balance details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDebtorSelect = (debtor: Debtor) => {
    setSelectedDebtor(debtor);
    loadBalanceDetails(debtor.id);
  };

  const handleSelectAnotherDebtor = () => {
    setSelectedDebtor(null);
    setBalanceDetails(null);
  };

  if (!selectedDebtor) {
    return (
      <div className="p-6">
        <DebtorSearch onSelect={handleDebtorSelect} />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Debtor Header */}
      <div className="flex items-center justify-between bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
        <div>
          <h2 className="text-xl font-bold text-gray-900">{selectedDebtor.name}</h2>
          <p className="text-sm text-gray-600">Account: {selectedDebtor.account_number}</p>
          <p className="text-sm text-gray-600">Type: {selectedDebtor.account_category === '' ? 'Balance Brought Forward' : selectedDebtor.account_category === 'O' ? 'Open Item' : 'Cash Customer'}</p>
        </div>
        <button
          onClick={handleSelectAnotherDebtor}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          View Another Debtor
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="p-8 text-center text-gray-500">Loading balance details...</div>
      ) : balanceDetails ? (
        <>
          {/* Account Balance Section */}
          <AccountBalance 
            debtor={selectedDebtor} 
            balance={balanceDetails} 
          />

          {/* Transaction Options */}
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 space-y-4">
            <h3 className="font-semibold text-gray-900">Transaction View Options</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  View Format
                </label>
                <select
                  value={viewFormat}
                  onChange={(e) => setViewFormat(e.target.value as 'details' | 'layout')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="details">Item Details, Quantity, Value & Profit</option>
                  <option value="layout">Transaction Layout</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Order Number
                </label>
                <input
                  type="text"
                  value={orderNumber}
                  onChange={(e) => setOrderNumber(e.target.value)}
                  placeholder="Optional"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                VAT Number
              </label>
              <input
                type="text"
                value={vatNumber}
                onChange={(e) => setVatNumber(e.target.value)}
                placeholder="Optional"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Sales Analysis Section */}
          <SalesAnalysis debtorId={selectedDebtor.id} />

          {/* Transaction History Section */}
          <TransactionHistory 
            debtorId={selectedDebtor.id} 
            debtorType={selectedDebtor.account_category}
            viewFormat={viewFormat}
            orderNumber={orderNumber}
            vatNumber={vatNumber}
          />

          {/* Footer Actions */}
          <div className="flex gap-3 justify-between pt-4 border-t border-gray-200">
            <button
              onClick={handleSelectAnotherDebtor}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              View Another Debtor
            </button>
            <button
              onClick={() => window.print()}
              className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
            >
              Print Enquiry
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
}

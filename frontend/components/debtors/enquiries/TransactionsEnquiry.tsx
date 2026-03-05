'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

type TransactionType = 'invoice' | 'creditnote' | 'cashsale' | 'cashreturn' | 'receipt' | 'discount' | 'interest' | 'debitjournal' | 'creditjournal' | 'laybye' | 'all';
type SubMenu = 'main' | 'grossprofit' | 'search' | 'daily' | 'cashup';

interface Transaction {
  id: number;
  transaction_type: string;
  transaction_number: string;
  date: string;
  details: string;
  sub_total: number;
  vat_amount: number;
  total_amount: number;
}

export default function TransactionsEnquiry() {
  const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedTypes, setSelectedTypes] = useState<TransactionType[]>(['all']);
  const [subMenu, setSubMenu] = useState<SubMenu>('main');
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const transactionTypes: { value: TransactionType; label: string }[] = [
    { value: 'invoice', label: 'Invoice' },
    { value: 'creditnote', label: 'Credit Note' },
    { value: 'cashsale', label: 'Cash Sale' },
    { value: 'cashreturn', label: 'Cash Return' },
    { value: 'receipt', label: 'Receipts' },
    { value: 'discount', label: 'Settled Discount' },
    { value: 'interest', label: 'Interest Charge' },
    { value: 'debitjournal', label: 'Debit Journal' },
    { value: 'creditjournal', label: 'Credit Journal' },
    { value: 'laybye', label: 'Laybye Sale' },
    { value: 'all', label: 'All Types' },
  ];

  const toggleType = (type: TransactionType) => {
    if (type === 'all') {
      setSelectedTypes(['all']);
    } else {
      const filtered = selectedTypes.filter(t => t !== 'all');
      if (filtered.includes(type)) {
        setSelectedTypes(filtered.filter(t => t !== type));
      } else {
        setSelectedTypes([...filtered, type]);
      }
    }
  };

  const generateReport = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.append('start_date', startDate);
      params.append('end_date', endDate);
      if (selectedTypes.length > 0 && !selectedTypes.includes('all')) {
        params.append('types', selectedTypes.join(','));
      }

      const response = await apiRequest(`/api/v1/debtors/transactions/?${params}`);
      const responseData = (response as any).data || (response as any);
      const txns = responseData.results || responseData;
      
      if (Array.isArray(txns)) {
        setTransactions(txns);
      }
    } catch (err) {
      setError('Failed to load transactions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-900">Transactions Enquiry</h2>

      {/* Sub-menu Navigation */}
      <div className="flex flex-wrap gap-2 border-b border-gray-200">
        <button
          onClick={() => setSubMenu('main')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            subMenu === 'main'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Transaction Listing
        </button>
        <button
          onClick={() => setSubMenu('grossprofit')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            subMenu === 'grossprofit'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Gross Profit
        </button>
        <button
          onClick={() => setSubMenu('search')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            subMenu === 'search'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Search
        </button>
        <button
          onClick={() => setSubMenu('daily')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            subMenu === 'daily'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Daily Totals
        </button>
        <button
          onClick={() => setSubMenu('cashup')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            subMenu === 'cashup'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Cashup Details
        </button>
      </div>

      {/* Filter Controls */}
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
        <h3 className="font-semibold text-gray-900">Filters</h3>
        
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Transaction Types</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {transactionTypes.map(type => (
              <label key={type.value} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedTypes.includes(type.value)}
                  onChange={() => toggleType(type.value)}
                  className="rounded"
                />
                <span className="text-sm text-gray-700">{type.label}</span>
              </label>
            ))}
          </div>
        </div>

        <button 
          onClick={generateReport}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Generate Report'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Content Area */}
      {subMenu === 'main' && <TransactionListingView transactions={transactions} loading={loading} />}
      {subMenu === 'grossprofit' && <GrossProfitView />}
      {subMenu === 'search' && <SearchView />}
      {subMenu === 'daily' && <DailyTotalsView />}
      {subMenu === 'cashup' && <CashupDetailsView />}
    </div>
  );
}

function TransactionListingView({ transactions, loading }: { transactions: Transaction[]; loading: boolean }) {
  return (
    <div className="space-y-4">
      <div className="flex gap-2 justify-end">
        <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium">
          Export to CSV
        </button>
        <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium">
          Print Detailed
        </button>
        <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium">
          Print Totals
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Type</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Transaction #</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Date</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Details</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Sub Total</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">VAT</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Total</th>
              </tr>
            </thead>
            <tbody>
              {transactions.length > 0 ? (
                transactions.map(txn => (
                  <tr key={txn.id} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{txn.transaction_type}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{txn.transaction_number}</td>
                    <td className="px-4 py-3 text-gray-700">{new Date(txn.date).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-gray-700">{txn.details}</td>
                    <td className="px-4 py-3 text-right text-gray-900">R{txn.sub_total.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-gray-900">R{txn.vat_amount.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-900">R{txn.total_amount.toFixed(2)}</td>
                  </tr>
                ))
              ) : (
                <tr className="border-b border-gray-200 hover:bg-gray-50">
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    {loading ? 'Loading...' : 'Click "Generate Report" to view transactions'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function GrossProfitView() {
  return (
    <div className="space-y-4">
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
        <h3 className="font-semibold text-gray-900">Gross Profit Filters</h3>
        
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Transaction #</label>
            <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Transaction #</label>
            <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Include Cash</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option>Yes</option>
              <option>No</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Specific Salesman/Area</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option>No</option>
              <option>Yes</option>
            </select>
          </div>
        </div>

        <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
          Generate Report
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Transaction #</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Date</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Account Name</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Net Value</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Profit Value</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Gross Profit %</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-200 hover:bg-gray-50">
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No data to display
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SearchView() {
  return (
    <div className="space-y-4">
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
        <h3 className="font-semibold text-gray-900">Search Transaction</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Transaction Number</label>
            <input type="text" placeholder="Enter transaction #" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Delivery Line Details</label>
            <input type="text" placeholder="Enter details" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
        </div>

        <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
          Search
        </button>
      </div>
    </div>
  );
}

function DailyTotalsView() {
  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Date</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Total Sales</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Total Returns</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">% of Sales</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Gross Profit Value</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Gross Profit %</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-200 hover:bg-gray-50">
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No daily totals to display
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex gap-2 justify-end">
        <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium">
          Print Listing
        </button>
        <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium">
          Export to CSV
        </button>
      </div>
    </div>
  );
}

function CashupDetailsView() {
  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Date</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Time</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Cash</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Cheque</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Voucher</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Speedpoint</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Rounding</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-200 hover:bg-gray-50">
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  No cashup details to display
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex gap-2 justify-end">
        <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium">
          Print Listing
        </button>
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

interface Transaction {
  id: number;
  transaction_type: string;
  transaction_number: string;
  transaction_date: string;
  amount: number;
  vat_amount: number;
  total_amount: number;
  reference: string;
  additional_reference: string;
}

interface TransactionHistoryProps {
  debtorId: number;
  debtorType: string;
  viewFormat: 'details' | 'layout';
  orderNumber: string;
  vatNumber: string;
}

export default function TransactionHistory({ 
  debtorId, 
  debtorType,
  viewFormat,
  orderNumber,
  vatNumber 
}: TransactionHistoryProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [filteredTransactions, setFilteredTransactions] = useState<Transaction[]>([]);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [searchNumber, setSearchNumber] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadTransactions();
  }, [debtorId]);

  useEffect(() => {
    // Filter transactions by number
    if (searchNumber.trim()) {
      const filtered = transactions.filter(tx =>
        tx.transaction_number.toLowerCase().includes(searchNumber.toLowerCase())
      );
      setFilteredTransactions(filtered);
      if (filtered.length > 0) {
        setSelectedTransaction(filtered[0]);
      }
    } else {
      setFilteredTransactions(transactions);
      if (transactions.length > 0) {
        setSelectedTransaction(transactions[0]);
      }
    }
  }, [searchNumber, transactions]);

  const loadTransactions = async () => {
    try {
      const response = await apiRequest(`/api/debtors/transactions/?debtor=${debtorId}`);
      
      if ((response as any).results) {
        setTransactions((response as any).results);
      } else if (Array.isArray(response)) {
        setTransactions(response);
      }
    } catch (err) {
      setError('Failed to load transactions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionTypeDisplay = (type: string) => {
    const types: Record<string, string> = {
      'INV': 'Invoice',
      'CRN': 'Credit Note',
      'CSH': 'Cash Sale',
      'CSR': 'Cash Return',
      'RCT': 'Receipt',
      'SDI': 'Settlement Discount',
      'INT': 'Interest Charge',
      'DBJ': 'Debit Journal',
      'CRJ': 'Credit Journal',
      'LAY': 'Laybye Sale',
    };
    return types[type] || type;
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'INV': 'bg-red-100 text-red-800',
      'CRN': 'bg-yellow-100 text-yellow-800',
      'RCT': 'bg-green-100 text-green-800',
      'INT': 'bg-orange-100 text-orange-800',
      'DBJ': 'bg-blue-100 text-blue-800',
      'CRJ': 'bg-purple-100 text-purple-800',
      'CSH': 'bg-green-100 text-green-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return <div className="p-4 text-gray-500">Loading transaction history...</div>;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Transaction History</h3>

      {/* Search Bar */}
      <div className="flex gap-2">
        <input
          type="text"
          value={searchNumber}
          onChange={(e) => setSearchNumber(e.target.value)}
          placeholder="Search by transaction number..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
        />
        <button
          onClick={() => setSearchNumber('')}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm font-medium"
        >
          Clear
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Selected Transaction Details */}
      {selectedTransaction && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">
              Transaction Details - {getTransactionTypeDisplay(selectedTransaction.transaction_type)}
            </h4>
          </div>

          {viewFormat === 'details' ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-gray-600 text-xs font-medium">Number</p>
                <p className="font-semibold text-gray-900">{selectedTransaction.transaction_number}</p>
              </div>
              <div>
                <p className="text-gray-600 text-xs font-medium">Date</p>
                <p className="font-semibold text-gray-900">{new Date(selectedTransaction.transaction_date).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-gray-600 text-xs font-medium">Amount (ex VAT)</p>
                <p className="font-semibold text-gray-900">R{selectedTransaction.amount.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-gray-600 text-xs font-medium">VAT</p>
                <p className="font-semibold text-gray-900">R{selectedTransaction.vat_amount.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-gray-600 text-xs font-medium">Total</p>
                <p className="font-semibold text-gray-900">R{selectedTransaction.total_amount.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-gray-600 text-xs font-medium">Reference</p>
                <p className="font-semibold text-gray-900">{selectedTransaction.reference || '-'}</p>
              </div>
            </div>
          ) : (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Transaction:</span>
                <span className="font-semibold">{selectedTransaction.transaction_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Date:</span>
                <span className="font-semibold">{new Date(selectedTransaction.transaction_date).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Amount:</span>
                <span className="font-semibold">R{selectedTransaction.total_amount.toFixed(2)}</span>
              </div>
              {selectedTransaction.additional_reference && (
                <div>
                  <span className="text-gray-600">Notes:</span>
                  <p className="font-semibold">{selectedTransaction.additional_reference}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Transactions List */}
      {filteredTransactions.length > 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100 border-b border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Type</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Number</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Date</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Amount</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Total</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map(transaction => (
                  <tr 
                    key={transaction.id}
                    onClick={() => setSelectedTransaction(transaction)}
                    className={`border-b border-gray-200 cursor-pointer hover:bg-gray-50 ${
                      selectedTransaction?.id === transaction.id ? 'bg-blue-50' : ''
                    }`}
                  >
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getTypeColor(transaction.transaction_type)}`}>
                        {transaction.transaction_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-900 font-medium">{transaction.transaction_number}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {new Date(transaction.transaction_date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-900">
                      R{transaction.amount.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-900">
                      R{transaction.total_amount.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center text-gray-600">
          No transactions found
        </div>
      )}

      {/* Footer Info */}
      {orderNumber || vatNumber ? (
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 text-sm space-y-1">
          {orderNumber && <p><span className="font-medium">Order Number:</span> {orderNumber}</p>}
          {vatNumber && <p><span className="font-medium">VAT Number:</span> {vatNumber}</p>}
        </div>
      ) : null}
    </div>
  );
}

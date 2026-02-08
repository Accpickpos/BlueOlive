'use client';

import { useState } from 'react';
import { ChevronRight, Package, RotateCcw, FileText, CreditCard, BookOpen, RefreshCw } from 'lucide-react';
import ReceivingStockForm from '@/components/creditors/transactions/ReceivingStockForm';
import ReturnsStockForm from '@/components/creditors/transactions/ReturnsStockForm';
import ExpenseInvoiceForm from '@/components/creditors/transactions/ExpenseInvoiceForm';
import ExpenseReturnForm from '@/components/creditors/transactions/ExpenseReturnForm';
import PaymentForm from '@/components/creditors/transactions/PaymentForm';
import JournalForm from '@/components/creditors/transactions/JournalForm';
import RFCForm from '@/components/creditors/transactions/RFCForm';
import TransactionsList from '@/components/creditors/transactions/TransactionsList';

type TransactionType = 
  | 'RECEIVING' 
  | 'RETURNS_STOCK' 
  | 'INVOICE_EXPENSE' 
  | 'RETURNS_EXPENSE' 
  | 'PAYMENT' 
  | 'JOURNAL' 
  | 'RFC' 
  | 'LIST';

const transactionTypes = [
  {
    id: 'RECEIVING',
    title: '1. Receiving - Stock Items',
    description: 'Goods Received Note - Updates Stock, Supplier Balance & VAT Controls',
    icon: Package,
    color: 'bg-blue-50 border-blue-200 hover:bg-blue-100',
  },
  {
    id: 'RETURNS_STOCK',
    title: '2. Returns - Stock Items',
    description: 'Credit Note / Goods Returned Note',
    icon: RotateCcw,
    color: 'bg-orange-50 border-orange-200 hover:bg-orange-100',
  },
  {
    id: 'INVOICE_EXPENSE',
    title: '3. Invoice Capture - Expense',
    description: 'E.g. Telkom, Stationery Accounts',
    icon: FileText,
    color: 'bg-green-50 border-green-200 hover:bg-green-100',
  },
  {
    id: 'RETURNS_EXPENSE',
    title: '4. Returns - Expense Categories',
    description: 'Credit Notes for Expense Accounts',
    icon: RotateCcw,
    color: 'bg-yellow-50 border-yellow-200 hover:bg-yellow-100',
  },
  {
    id: 'PAYMENT',
    title: '5. Post Payment(s)',
    description: 'Record Supplier Payments',
    icon: CreditCard,
    color: 'bg-purple-50 border-purple-200 hover:bg-purple-100',
  },
  {
    id: 'JOURNAL',
    title: '6. Journal Entries',
    description: 'Debit/Credit Journal Transactions',
    icon: BookOpen,
    color: 'bg-indigo-50 border-indigo-200 hover:bg-indigo-100',
  },
  {
    id: 'RFC',
    title: '7. RFC Controls',
    description: 'Return for Credit - Stock Replacement or Credit',
    icon: RefreshCw,
    color: 'bg-pink-50 border-pink-200 hover:bg-pink-100',
  },
];

export default function CreditorsTransactionsPage() {
  const [selectedType, setSelectedType] = useState<TransactionType | null>(null);

  const renderForm = () => {
    switch (selectedType) {
      case 'RECEIVING':
        return <ReceivingStockForm onComplete={() => setSelectedType('LIST')} />;
      case 'RETURNS_STOCK':
        return <ReturnsStockForm onComplete={() => setSelectedType('LIST')} />;
      case 'INVOICE_EXPENSE':
        return <ExpenseInvoiceForm onComplete={() => setSelectedType('LIST')} />;
      case 'RETURNS_EXPENSE':
        return <ExpenseReturnForm onComplete={() => setSelectedType('LIST')} />;
      case 'PAYMENT':
        return <PaymentForm onComplete={() => setSelectedType('LIST')} />;
      case 'JOURNAL':
        return <JournalForm onComplete={() => setSelectedType('LIST')} />;
      case 'RFC':
        return <RFCForm onComplete={() => setSelectedType('LIST')} />;
      case 'LIST':
        return <TransactionsList onBack={() => setSelectedType(null)} />;
      default:
        return null;
    }
  };

  if (selectedType) {
    return (
      <div className="p-6">
        <div className="mb-4">
          <button
            onClick={() => setSelectedType(null)}
            className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2"
          >
            ← Back to Menu
          </button>
        </div>
        {renderForm()}
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Creditors - Transactions Management
        </h1>
        <p className="text-gray-600">
          Select a transaction type to record supplier transactions
        </p>
      </div>

      {/* View Transactions Button */}
      <div className="mb-6">
        <button
          onClick={() => setSelectedType('LIST')}
          className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 transition-all duration-200 flex items-center justify-between"
        >
          <span>View All Transactions</span>
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Transaction Types Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-4">
        {transactionTypes.map((type) => {
          const Icon = type.icon;
          return (
            <button
              key={type.id}
              onClick={() => setSelectedType(type.id as TransactionType)}
              className={`p-6 border-2 rounded-lg transition-all duration-200 text-left hover:shadow-md ${type.color}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Icon className="w-6 h-6" />
                    <h3 className="font-bold text-gray-900">{type.title}</h3>
                  </div>
                  <p className="text-sm text-gray-600 ml-9">{type.description}</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0 ml-4" />
              </div>
            </button>
          );
        })}
      </div>

      {/* Quick Reference */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">Transaction Types Overview</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <strong>Stock Transactions:</strong> Receiving and Returns update inventory and supplier balances</li>
          <li>• <strong>Expense Transactions:</strong> Invoice Capture and Returns for operational expenses</li>
          <li>• <strong>Payments:</strong> Record cash payments to suppliers</li>
          <li>• <strong>Journals:</strong> Adjust supplier balances with debit/credit journals</li>
          <li>• <strong>RFC:</strong> Manage return for credit items (stock replacement or credit notes)</li>
        </ul>
      </div>
    </div>
  );
}

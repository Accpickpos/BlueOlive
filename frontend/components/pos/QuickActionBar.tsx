'use client';

import { useState } from 'react';
import { Search, Users, CreditCard, Package, X } from 'lucide-react';
import DebtorSearch from '@/components/debtors/enquiries/DebtorSearch';
import { CreditorSearch } from '@/components/creditors/CreditorSearch';
import { StockItemPicker } from '@/components/pos/StockItemPicker';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface QuickActionBarProps {
  onSelectDebtor?: (debtor: { account_number: string; name: string; id: number }) => void;
  onSelectCreditor?: (creditor: { account_number: string; name: string; id: number }) => void;
  onSelectStockItem?: (item: { stock_code: string; description: string }) => void;
  mode?: 'all' | 'debtor' | 'creditor' | 'stock';
}

interface Debtor {
  id: number;
  name: string;
  account_number: string;
}

interface StockItem {
  stock_code: string;
  description: string;
}

export function QuickActionBar({ 
  onSelectDebtor, 
  onSelectCreditor, 
  onSelectStockItem,
  mode = 'all'
}: QuickActionBarProps) {
  const [activeTab, setActiveTab] = useState<'debtor' | 'creditor' | 'stock'>('stock');
  const [isExpanded, setIsExpanded] = useState(false);

  // Show nothing if mode is restricted
  if (mode === 'debtor' && !onSelectDebtor) return null;
  if (mode === 'creditor' && !onSelectCreditor) return null;
  if (mode === 'stock' && !onSelectStockItem) return null;

  const tabs = [
    { id: 'stock', label: 'Stock', icon: Package, show: mode === 'all' || mode === 'stock' },
    { id: 'debtor', label: 'Debtor', icon: Users, show: mode === 'all' || mode === 'debtor' },
    { id: 'creditor', label: 'Creditor', icon: CreditCard, show: mode === 'all' || mode === 'creditor' },
  ] as const;

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 mb-4">
      {/* Header */}
      <div 
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-gray-500" />
          <span className="font-medium text-sm text-gray-700">Quick Search</span>
        </div>
        <div className="flex items-center gap-2">
          {isExpanded && (
            <span className="text-xs text-gray-500">Click to collapse</span>
          )}
          <span className="text-gray-400 transform transition-transform" style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>
            ▼
          </span>
        </div>
      </div>

      {/* Expanded Search Area */}
      {isExpanded && (
        <div className="border-t border-gray-200">
          {/* Tabs */}
          <div className="flex border-b border-gray-200">
            {tabs.map((tab) => (
              tab.show && (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <tab.icon className="h-4 w-4" />
                  {tab.label}
                </button>
              )
            ))}
          </div>

          {/* Search Content */}
          <div className="p-4">
            {activeTab === 'stock' && onSelectStockItem && (
              <StockItemPicker
                onSelect={(item) => {
                  onSelectStockItem({
                    stock_code: item.stock_code,
                    description: item.description,
                  });
                  setIsExpanded(false);
                }}
                placeholder="Search stock by code, barcode or description..."
              />
            )}

            {activeTab === 'debtor' && onSelectDebtor && (
              <DebtorSearch
                onSelect={(debtor: Debtor) => {
                  onSelectDebtor({
                    account_number: debtor.account_number,
                    name: debtor.name,
                    id: debtor.id,
                  });
                  setIsExpanded(false);
                }}
              />
            )}

            {activeTab === 'creditor' && onSelectCreditor && (
              <CreditorSearch
                onSelect={(creditor) => {
                  onSelectCreditor({
                    account_number: creditor.account_number,
                    name: creditor.name,
                    id: creditor.id,
                  });
                  setIsExpanded(false);
                }}
                placeholder="Search creditors by account number or name..."
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Compact inline version for forms
interface InlineSearchButtonProps {
  type: 'debtor' | 'creditor' | 'stock';
  onSelect: (data: any) => void;
}

export function InlineSearchButton({ type, onSelect }: InlineSearchButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  const iconMap = {
    debtor: Users,
    creditor: CreditCard,
    stock: Package,
  };

  const labelMap = {
    debtor: 'Select Debtor',
    creditor: 'Select Creditor',
    stock: 'Select Item',
  };

  const Icon = iconMap[type];

  return (
    <>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-1"
      >
        <Icon className="h-4 w-4" />
        Search
      </Button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-lg max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-semibold">{labelMap[type]}</h3>
              <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <CardContent className="p-4 overflow-y-auto max-h-[60vh]">
              {type === 'stock' && (
                <div className="space-y-4">
                  <StockItemPicker
                    onSelect={(item: StockItem) => {
                      onSelect(item);
                      setIsOpen(false);
                    }}
                  />
                </div>
              )}
              {type === 'debtor' && (
                <DebtorSearch
                  onSelect={(debtor: Debtor) => {
                    onSelect(debtor);
                    setIsOpen(false);
                  }}
                />
              )}
              {type === 'creditor' && (
                <CreditorSearch
                  onSelect={(creditor) => {
                    onSelect(creditor);
                    setIsOpen(false);
                  }}
                />
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}

export default QuickActionBar;

'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, User, X, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';

interface DebtorPickerProps {
  onSelect: (debtor: {
    account_number: string;
    name: string;
    balance: number;
    credit_limit: number;
  }) => void;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
}

export function DebtorPicker({ 
  onSelect, 
  label = 'Customer', 
  placeholder = 'Search customers...',
  disabled = false 
}: DebtorPickerProps) {
  const { user } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [selectedName, setSelectedName] = useState('');

  // Load items when modal opens
  useEffect(() => {
    if (isOpen && results.length === 0) {
      loadAllItems();
    }
  }, [isOpen]);

  // Search when query changes
  useEffect(() => {
    if (!isOpen) return;
    
    const timer = setTimeout(async () => {
      if (!query.trim()) {
        loadAllItems();
        return;
      }
      
      if (query.length < 2) return; // Need at least 2 chars
      
      setIsLoading(true);
      try {
        const response = await posAPI.searchDebtors(query);
        setResults(response.results || []);
        setSelectedIndex(0);
      } catch (error) {
        console.error('Error searching debtors:', error);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, isOpen, posAPI]);

  const loadAllItems = async () => {
    setIsLoading(true);
    try {
      const response = await posAPI.searchDebtors('');
      setResults(response.results || []);
      setSelectedIndex(0);
    } catch (error) {
      console.error('Error loading debtors:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelect = (debtor: any) => {
    // Handle different field name formats from API (customer_number is the actual field from backend)
    const accountNum = debtor.customer_number || debtor.account_number || debtor.accountNumber || debtor.id || '';
    const selectData = {
      account_number: accountNum,
      name: debtor.name || debtor.name || '',
      balance: Number(debtor.balance || debtor.balance_due || 0),
      credit_limit: Number(debtor.credit_limit || 0),
    };
    onSelect(selectData);
    setSelectedName(debtor.name);
    setIsOpen(false);
    setQuery('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => (prev < results.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : prev));
        break;
      case 'Enter':
        e.preventDefault();
        if (results[selectedIndex]) {
          handleSelect(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setQuery('');
    setResults([]);
  };

  return (
    <>
      {/* Button to open modal - show selected item if any */}
      <div className="flex gap-2 items-center">
        <Button
          type="button"
          variant="outline"
          onClick={() => !disabled && setIsOpen(true)}
          className="w-full justify-start text-left font-normal h-10"
          disabled={disabled}
        >
          <User className="mr-2 h-4 w-4" />
          {selectedName || placeholder}
        </Button>
      </div>

      {/* Modal Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-2xl max-h-[80vh] flex flex-col">
            <CardHeader className="flex-shrink-0">
              <div className="flex items-center justify-between">
                <CardTitle>Select Customer</CardTitle>
                <Button variant="ghost" size="sm" onClick={handleClose}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <div className="relative mt-2">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Search by account number or name..."
                  className="pl-10"
                  autoFocus
                />
              </div>
            </CardHeader>
            
            <CardContent className="flex-1 overflow-y-auto p-0">
              {isLoading ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                </div>
              ) : results.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  {query.length < 2 ? 'Type at least 2 characters to search' : 'No customers found'}
                </div>
              ) : (
                <div className="divide-y">
                  {results.map((debtor, index) => (
                    <button
                      key={debtor.account_number || debtor.id || `debtor-${index}`}
                      onClick={() => handleSelect(debtor)}
                      onMouseEnter={() => setSelectedIndex(index)}
                      className={`w-full text-left px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors ${
                        index === selectedIndex ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-gray-400 flex-shrink-0" />
                          <span className="font-medium text-gray-900">
                            {debtor.account_number}
                          </span>
                        </div>
                        <p className="text-sm text-gray-500 truncate ml-6">
                          {debtor.name}
                        </p>
                      </div>
                      <div className="text-right ml-4 flex-shrink-0">
                        <div className="font-medium text-red-600">
                          R{Number(debtor.balance || debtor.balance_due || 0).toFixed(2)}
                        </div>
                        <div className="text-xs text-gray-400">
                          Balance
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
            
            <div className="p-2 border-t bg-gray-50 text-xs text-gray-500 text-center">
              Use arrow keys to navigate, Enter to select, Escape to close
            </div>
          </Card>
        </div>
      )}
    </>
  );
}

export default DebtorPicker;

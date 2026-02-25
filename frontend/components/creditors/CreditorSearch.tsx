'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, CreditCard, X, Loader2, Building2 } from 'lucide-react';
import { creditorsApi } from '@/lib/creditorsApi';
import { CreditorAccount } from '@/lib/types/creditors';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';

interface CreditorSearchProps {
  onSelect: (creditor: {
    id: number;
    account_number: string;
    name: string;
    balance?: number;
    credit_limit?: number;
  }) => void;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
}

export function CreditorSearch({ 
  onSelect, 
  label = 'Creditor', 
  placeholder = 'Search by account number or name...',
  disabled = false 
}: CreditorSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<CreditorAccount[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounced search
  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const response = await creditorsApi.accounts.list({
          search: query,
          page_size: 10,
          is_active: true,
        });
        setResults(response.results || []);
        setIsOpen(true);
        setSelectedIndex(0);
      } catch (error) {
        console.error('Error searching creditors:', error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = useCallback((creditor: CreditorAccount) => {
    onSelect({
      id: creditor.id,
      account_number: creditor.supplier_number,
      name: creditor.name,
      balance: creditor.total_outstanding_balance,
    });
    setQuery('');
    setIsOpen(false);
    setResults([]);
  }, [onSelect]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;

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

  return (
    <div className="relative" ref={wrapperRef}>
      {label && (
        <label className="block text-sm font-medium mb-1.5 text-gray-700">
          {label}
        </label>
      )}
      
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 2 && results.length > 0 && setIsOpen(true)}
          placeholder={placeholder}
          disabled={disabled}
          className="pl-10 pr-10"
          autoComplete="off"
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-gray-400" />
        )}
        {query && !isLoading && (
          <button
            onClick={() => {
              setQuery('');
              setResults([]);
              setIsOpen(false);
              inputRef.current?.focus();
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2"
          >
            <X className="h-4 w-4 text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <Card className="absolute z-50 w-full mt-1 shadow-lg border-gray-200 max-h-80 overflow-y-auto">
          <CardContent className="p-0">
            {results.map((creditor, index) => (
              <button
                key={creditor.id}
                onClick={() => handleSelect(creditor)}
                className={`w-full text-left px-4 py-3 flex items-center justify-between hover:bg-gray-50 border-b border-gray-100 last:border-0 transition-colors ${
                  index === selectedIndex ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <CreditCard className="h-4 w-4 text-gray-400 flex-shrink-0" />
                    <span className="font-medium text-gray-900">
                      {creditor.supplier_number}
                    </span>
                    <span className="text-gray-500 truncate">
                      {creditor.name}
                    </span>
                  </div>
                  {creditor.contact_person && (
                    <p className="text-sm text-gray-400 ml-6">
                      Contact: {creditor.contact_person}
                    </p>
                  )}
                </div>
                <div className="text-right ml-4 flex-shrink-0">
                  <div className={`font-medium ${creditor.total_outstanding_balance > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    R{creditor.total_outstanding_balance.toFixed(2)}
                  </div>
                </div>
              </button>
            ))}
          </CardContent>
        </Card>
      )}

      {isOpen && query.length >= 2 && results.length === 0 && !isLoading && (
        <Card className="absolute z-50 w-full mt-1 shadow-lg border-gray-200">
          <CardContent className="p-4 text-center text-gray-500">
            No creditors found for "{query}"
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default CreditorSearch;

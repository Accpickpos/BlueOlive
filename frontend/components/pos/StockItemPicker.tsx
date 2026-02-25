'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Package, X, Loader2 } from 'lucide-react';
import { stockControlApi } from '@/lib/stockControlApi';
import type { StockItem } from '@/lib/types/stockControl';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface StockItemPickerProps {
  onSelect: (item: {
    stock_code: string;
    description: string;
    selling_price: number;
    cost_price: number;
    tax_code: string | number;
    tax_code_detail?: { code: string; rate?: number };
  }) => void;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
}

export function StockItemPicker({ 
  onSelect, 
  label = 'Stock Item', 
  placeholder = 'Search stock items...',
  disabled = false 
}: StockItemPickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<StockItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [itemCode, setItemCode] = useState('');

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
      
      setIsLoading(true);
      try {
        const response = await stockControlApi.stockItems.list({
          search: query,
          page_size: 50,
          is_active: true,
        });
        setResults(response.results || []);
        setSelectedIndex(0);
      } catch (error) {
        console.error('Error searching:', error);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, isOpen]);

  const loadAllItems = async () => {
    setIsLoading(true);
    try {
      const response = await stockControlApi.stockItems.list({
        page_size: 50,
        is_active: true,
      });
      setResults(response.results || []);
      setSelectedIndex(0);
    } catch (error) {
      console.error('Error loading items:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelect = (item: StockItem) => {
    console.log('Selected item:', item);
    const selectData = {
      stock_code: item.stock_code,
      description: item.description,
      selling_price: Number(item.selling_price_1 || 0),
      cost_price: Number(item.average_cost || item.cost_price || 0),
      tax_code: String(item.tax_code),
      tax_code_detail: item.tax_code_detail,
    };
    console.log('Calling onSelect with:', selectData);
    onSelect(selectData);
    setItemCode(item.stock_code);
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

  return (
    <>
      {/* Button to open modal - show selected item if any */}
      <div className="flex gap-2 items-center">
        <Button
          type="button"
          variant="outline"
          onClick={() => setIsOpen(true)}
          className="w-full justify-start text-left font-normal h-10"
        >
          <Package className="mr-2 h-4 w-4" />
          {itemCode || placeholder}
        </Button>
      </div>

      {/* Modal Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-2xl max-h-[80vh] flex flex-col">
            <CardHeader className="flex-shrink-0">
              <div className="flex items-center justify-between">
                <CardTitle>Select Stock Item</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)}>
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
                  placeholder="Search by code, barcode or description..."
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
                  No items found
                </div>
              ) : (
                <div className="divide-y">
                  {results.map((item, index) => (
                    <button
                      key={item.stock_code}
                      onClick={() => handleSelect(item)}
                      onMouseEnter={() => setSelectedIndex(index)}
                      className={`w-full text-left px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors ${
                        index === selectedIndex ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <Package className="h-4 w-4 text-gray-400 flex-shrink-0" />
                          <span className="font-medium text-gray-900">
                            {item.stock_code}
                          </span>
                          {item.barcode && (
                            <span className="text-xs text-gray-400">({item.barcode})</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 truncate ml-6">
                          {item.description}
                        </p>
                      </div>
                      <div className="text-right ml-4 flex-shrink-0">
                        <div className="font-medium text-green-600">
                          R{Number(item.selling_price_1 || 0).toFixed(2)}
                        </div>
                        <div className="text-xs text-gray-400">
                          Cost: R{Number(item.average_cost || item.cost_price || 0).toFixed(2)}
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

export default StockItemPicker;

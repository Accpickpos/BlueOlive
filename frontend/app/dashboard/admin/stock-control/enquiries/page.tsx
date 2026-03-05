'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getStockItems, getStockSummary } from '@/lib/stockApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Loader, Package, Search, TrendingUp, History, 
  DollarSign, ArrowRight
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function StockControlEnquiriesPage() {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['stock-summary'],
    queryFn: getStockSummary,
    staleTime: 5 * 60 * 1000,
  });

  // Handle search when user types
  const handleSearch = async (value: string) => {
    setSearchTerm(value);
    if (value.length >= 2) {
      setIsSearching(true);
      try {
        const result = await getStockItems({ search: value, page_size: 10 });
        setSearchResults(result.results || []);
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    } else {
      setSearchResults([]);
    }
  };

  const handleItemClick = (stockCode: string) => {
    router.push(`/dashboard/admin/stock-control/enquiries/item?code=${stockCode}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Stock Control - Enquiries</h1>
        <p className="text-gray-600 mt-1">Search and enquire about stock items</p>
      </div>

      {/* Quick Search */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">Quick Item Search</h2>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <Input
            placeholder="Search by stock code or description..."
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-10 h-12 text-lg"
          />
          {isSearching && (
            <Loader className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 animate-spin text-blue-600" />
          )}
        </div>

        {/* Search Results Dropdown */}
        {searchResults.length > 0 && (
          <div className="mt-2 border rounded-lg divide-y max-h-64 overflow-y-auto">
            {searchResults.map((item: any) => (
              <button
                key={item.stock_code}
                onClick={() => handleItemClick(item.stock_code)}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between"
              >
                <div>
                  <span className="font-mono font-medium">{item.stock_code}</span>
                  <span className="text-gray-500 ml-2">{item.description}</span>
                </div>
                <div className="text-right">
                  <span className="text-sm text-gray-600">QOH: </span>
                  <span className={`font-medium ${item.quantity_on_hand <= 0 ? 'text-red-600' : item.quantity_on_hand <= item.reorder_quantity ? 'text-amber-600' : 'text-green-600'}`}>
                    {item.quantity_on_hand?.toFixed(2) || 0}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}

        {searchTerm.length >= 2 && searchResults.length === 0 && !isSearching && (
          <p className="mt-2 text-gray-500 text-sm">No items found matching "{searchTerm}"</p>
        )}
      </Card>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-6 border-l-4 border-l-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 uppercase">Total Stock Value</p>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  R {summary.total_value?.toLocaleString('en-ZA', { maximumFractionDigits: 0 }) || 0}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-green-200" />
            </div>
          </Card>

          <Card className="p-6 border-l-4 border-l-amber-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 uppercase">Low Stock Items</p>
                <p className="text-2xl font-bold text-amber-600 mt-1">
                  {summary.low_stock_count || 0}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-amber-200" />
            </div>
          </Card>

          <Card className="p-6 border-l-4 border-l-red-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 uppercase">Out of Stock</p>
                <p className="text-2xl font-bold text-red-600 mt-1">
                  {summary.out_of_stock_count || 0}
                </p>
              </div>
              <Package className="w-8 h-8 text-red-200" />
            </div>
          </Card>
        </div>
      )}

      {/* Enquiry Types */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Enquiry Types</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link href="/dashboard/admin/stock-control/enquiries/item">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <Package className="w-10 h-10 text-blue-600 mb-3" />
              <h3 className="font-bold text-lg">Individual Item</h3>
              <p className="text-sm text-gray-600 mt-1">View detailed information for a specific stock item</p>
              <div className="mt-4 flex items-center text-blue-600 text-sm font-medium">
                Go to enquiry <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/enquiries/movements">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <TrendingUp className="w-10 h-10 text-purple-600 mb-3" />
              <h3 className="font-bold text-lg">Stock Movements</h3>
              <p className="text-sm text-gray-600 mt-1">View transaction history and movement patterns</p>
              <div className="mt-4 flex items-center text-purple-600 text-sm font-medium">
                Go to enquiry <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/enquiries/valuation">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <DollarSign className="w-10 h-10 text-green-600 mb-3" />
              <h3 className="font-bold text-lg">Stock Valuation</h3>
              <p className="text-sm text-gray-600 mt-1">View current stock value by category or department</p>
              <div className="mt-4 flex items-center text-green-600 text-sm font-medium">
                Go to enquiry <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>

          <Link href="/dashboard/admin/stock-control/enquiries/trends">
            <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
              <History className="w-10 h-10 text-amber-600 mb-3" />
              <h3 className="font-bold text-lg">Sales Trends</h3>
              <p className="text-sm text-gray-600 mt-1">Analyze historical sales data and patterns</p>
              <div className="mt-4 flex items-center text-amber-600 text-sm font-medium">
                Go to enquiry <ArrowRight className="w-4 h-4 ml-1" />
              </div>
            </Card>
          </Link>
        </div>
      </div>

      {/* Quick Tips */}
      <Card className="p-6 bg-gray-50">
        <h3 className="font-semibold mb-2">Quick Tips</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Use the search bar above to quickly find any stock item</li>
          <li>• Click on any item in the search results to view its full details</li>
          <li>• Individual Item enquiry shows pricing, transactions, and current stock levels</li>
          <li>• Stock Movements tracks all incoming and outgoing stock transactions</li>
        </ul>
      </Card>
    </div>
  );
}

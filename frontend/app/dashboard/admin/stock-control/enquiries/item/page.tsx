'use client';

import { useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { getStockItem, getStockItemPricing, getStockItemTransactions, getStockItems } from '@/lib/stockApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Loader, Search, Package, DollarSign, TrendingUp, 
  ArrowLeft, AlertTriangle, Calendar, ArrowDown, ArrowUp
} from 'lucide-react';
import Link from 'next/link';

function ItemEnquiryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialCode = searchParams.get('code') || '';
  
  const [stockCode, setStockCode] = useState(initialCode);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  // Fetch stock item details
  const { data: stockItem, isLoading: itemLoading, error: itemError } = useQuery({
    queryKey: ['stock-item', stockCode],
    queryFn: () => getStockItem(stockCode),
    enabled: !!stockCode,
    staleTime: 30 * 1000,
  });

  // Fetch pricing information
  const { data: pricing, isLoading: pricingLoading } = useQuery({
    queryKey: ['stock-item-pricing', stockCode],
    queryFn: () => getStockItemPricing(stockCode),
    enabled: !!stockCode,
    staleTime: 30 * 1000,
  });

  // Fetch transaction history
  const { data: transactions, isLoading: txLoading } = useQuery({
    queryKey: ['stock-item-transactions', stockCode],
    queryFn: () => getStockItemTransactions(stockCode, { page_size: 20 }),
    enabled: !!stockCode,
    staleTime: 30 * 1000,
  });

  // Search for stock items
  const handleSearch = async (value: string) => {
    setSearchTerm(value);
    if (value.length >= 2) {
      try {
        const result = await getStockItems({ search: value, page_size: 10 });
        setSearchResults(result.results || []);
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
      }
    } else {
      setSearchResults([]);
    }
  };

  const handleItemSelect = (code: string) => {
    setStockCode(code);
    setSearchTerm('');
    setSearchResults([]);
    router.push(`/dashboard/admin/stock-control/enquiries/item?code=${code}`);
  };

  const handleEnquire = () => {
    if (stockCode) {
      router.push(`/dashboard/admin/stock-control/enquiries/item?code=${stockCode}`);
    }
  };

  // Loading state
  if (itemLoading || pricingLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/stock-control/enquiries">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Individual Item Enquiry</h1>
          <p className="text-gray-600 mt-1">View detailed information for a specific stock item</p>
        </div>
      </div>

      {/* Stock Code Search */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">Find Stock Item</h2>
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              placeholder="Enter stock code or search by description..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              className="pl-10"
            />
            {searchResults.length > 0 && (
              <div className="absolute z-10 w-full mt-1 border rounded-lg divide-y bg-white shadow-lg max-h-64 overflow-y-auto">
                {searchResults.map((item: any) => (
                  <button
                    key={item.stock_code}
                    onClick={() => handleItemSelect(item.stock_code)}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50"
                  >
                    <span className="font-mono font-medium">{item.stock_code}</span>
                    <span className="text-gray-500 ml-2">{item.description}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <Button onClick={handleEnquire} disabled={!stockCode}>
            Enquire
          </Button>
        </div>
      </Card>

      {/* Item Details */}
      {stockItem && !itemError && (
        <>
          {/* Basic Info */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="p-6">
              <h3 className="font-semibold text-lg mb-4 flex items-center">
                <Package className="w-5 h-5 mr-2 text-blue-600" />
                Item Details
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Stock Code</p>
                  <p className="font-mono font-bold text-lg">{stockItem.stock_code}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Description</p>
                  <p className="font-medium">{stockItem.description}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Supplier Code</p>
                  <p className="font-mono">{stockItem.supplier_code || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Department</p>
                  <p>{stockItem.department_detail?.name || stockItem.department || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Bin Number</p>
                  <p>{stockItem.bin_number || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Tax Code</p>
                  <p>{stockItem.tax_code || '-'}</p>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="font-semibold text-lg mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-green-600" />
                Stock Levels
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Quantity on Hand</p>
                  <p className={`text-2xl font-bold ${stockItem.quantity_on_hand <= 0 ? 'text-red-600' : stockItem.quantity_on_hand <= stockItem.reorder_quantity ? 'text-amber-600' : 'text-green-600'}`}>
                    {stockItem.quantity_on_hand?.toFixed(2) || '0.00'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Reorder Quantity</p>
                  <p className="font-medium">{stockItem.reorder_quantity?.toFixed(2) || '0.00'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Allocated</p>
                  <p className="font-medium">{stockItem.quantity_allocated?.toFixed(2) || '0.00'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Available</p>
                  <p className="font-medium">{((stockItem.quantity_on_hand || 0) - (stockItem.quantity_allocated || 0)).toFixed(2)}</p>
                </div>
                <div className="pt-2">
                  {stockItem.quantity_on_hand <= 0 ? (
                    <div className="flex items-center text-red-600 text-sm">
                      <AlertTriangle className="w-4 h-4 mr-1" />
                      Out of Stock
                    </div>
                  ) : stockItem.quantity_on_hand <= stockItem.reorder_quantity ? (
                    <div className="flex items-center text-amber-600 text-sm">
                      <AlertTriangle className="w-4 h-4 mr-1" />
                      Low Stock
                    </div>
                  ) : (
                    <div className="flex items-center text-green-600 text-sm">
                      <Package className="w-4 h-4 mr-1" />
                      In Stock
                    </div>
                  )}
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="font-semibold text-lg mb-4 flex items-center">
                <DollarSign className="w-5 h-5 mr-2 text-purple-600" />
                Pricing Information
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Cost Price</p>
                  <p className="text-xl font-bold">R {stockItem.cost_price?.toFixed(2) || '0.00'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Selling Price 1</p>
                  <p className="font-medium">R {stockItem.selling_price_1?.toFixed(2) || '0.00'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Selling Price 2</p>
                  <p className="font-medium">R {stockItem.selling_price_2?.toFixed(2) || '0.00'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Selling Price 3</p>
                  <p className="font-medium">R {stockItem.selling_price_3?.toFixed(2) || '0.00'}</p>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="font-semibold text-lg mb-4 flex items-center">
                <DollarSign className="w-5 h-5 mr-2 text-purple-600" />
                Pricing Information
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Cost Price</p>
                  <p className="text-xl font-bold">R {stockItem.cost_price?.toFixed(2) || '0.00'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Selling Price 1</p>
                  <p className="font-medium">R {stockItem.selling_price_1?.toFixed(2) || '0.00'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Selling Price 2</p>
                  <p className="font-medium">R {stockItem.selling_price_2?.toFixed(2) || '0.00'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Selling Price 3</p>
                  <p className="font-medium">R {stockItem.selling_price_3?.toFixed(2) || '0.00'}</p>
                </div>
                {pricing?.active_special_deal && (
                  <div className="pt-2 border-t">
                    <p className="text-sm text-amber-600 font-medium">Active Special Deal!</p>
                    <p className="text-sm">R {pricing.active_special_deal.special_selling_price_1?.toFixed(2)}</p>
                    <p className="text-xs text-gray-500">
                      Until {pricing.active_special_deal.end_date}
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* Transaction History */}
          <Card className="p-6">
            <h3 className="font-semibold text-lg mb-4 flex items-center">
              <Calendar className="w-5 h-5 mr-2 text-amber-600" />
              Recent Transactions
            </h3>
            {txLoading ? (
              <div className="flex justify-center py-8">
                <Loader className="w-6 h-6 animate-spin text-blue-600" />
              </div>
            ) : transactions?.results && transactions.results.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2">Date</th>
                      <th className="text-left py-3 px-2">Type</th>
                      <th className="text-right py-3 px-2">Qty</th>
                      <th className="text-right py-3 px-2">Unit Cost</th>
                      <th className="text-right py-3 px-2">Total</th>
                      <th className="text-left py-3 px-2">Reference</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.results.map((tx: any) => (
                      <tr key={tx.id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-2">
                          {tx.transaction_date ? new Date(tx.transaction_date).toLocaleDateString('en-ZA') : '-'}
                        </td>
                        <td className="py-3 px-2">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            tx.transaction_type === 'IN' || tx.transaction_type === 'INCOMING' 
                              ? 'bg-green-100 text-green-800' 
                              : tx.transaction_type === 'OUT' || tx.transaction_type === 'OUTGOING'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {tx.transaction_type}
                          </span>
                        </td>
                        <td className={`py-3 px-2 text-right font-medium ${
                          tx.quantity > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {tx.quantity > 0 ? '+' : ''}{tx.quantity?.toFixed(2)}
                        </td>
                        <td className="py-3 px-2 text-right">
                          R {tx.unit_cost?.toFixed(2) || '0.00'}
                        </td>
                        <td className="py-3 px-2 text-right">
                          R {((tx.quantity || 0) * (tx.unit_cost || 0)).toFixed(2)}
                        </td>
                        <td className="py-3 px-2 text-gray-600">
                          {tx.reference || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No transactions found for this item</p>
            )}
          </Card>

          {/* Future Pricing */}
          {pricing?.future_prices && pricing.future_prices.length > 0 && (
            <Card className="p-6">
              <h3 className="font-semibold text-lg mb-4">Future Pricing</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2">Effective Date</th>
                      <th className="text-right py-3 px-2">New Price</th>
                      <th className="text-left py-3 px-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pricing.future_prices.map((fp: any, idx: number) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-2">
                          {fp.effective_date ? new Date(fp.effective_date).toLocaleDateString('en-ZA') : '-'}
                        </td>
                        <td className="py-3 px-2 text-right font-medium">
                          R {fp.new_price?.toFixed(2)}
                        </td>
                        <td className="py-3 px-2">
                          <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">
                            Pending
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}

      {/* No item selected */}
      {!stockCode && (
        <Card className="p-12 text-center">
          <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">Enter a stock code above to view item details</p>
        </Card>
      )}

      {/* Error state */}
      {itemError && stockCode && (
        <Card className="p-6 border-red-200 bg-red-50">
          <div className="flex items-center text-red-600">
            <AlertTriangle className="w-5 h-5 mr-2" />
            <p>Stock item "{stockCode}" not found. Please check the code and try again.</p>
          </div>
        </Card>
      )}
    </div>
  );
}

export default function ItemEnquiryPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    }>
      <ItemEnquiryContent />
    </Suspense>
  );
}

'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { getStockItems } from '@/lib/stockApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Loader, ArrowLeft, Plus, CheckCircle,
  Package, Activity, Search
} from 'lucide-react';
import Link from 'next/link';

export default function StocktakePage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('list');
  const [selectedTakeId, setSelectedTakeId] = useState<number | null>(null);
  
  // Form state
  const [newTake, setNewTake] = useState({
    stock_take_date: new Date().toISOString().split('T')[0],
    description: '',
  });

  // Count form state
  const [countForm, setCountForm] = useState({
    stock_code: '',
    quantity_counted: 0,
  });
  const [selectedStockItem, setSelectedStockItem] = useState<any>(null);
  const [searchResults, setSearchResults] = useState<any[]>([]);

  // Fetch all stock takes
  const { data: stockTakes, isLoading: takesLoading } = useQuery({
    queryKey: ['stock-takes'],
    queryFn: () => stockControlApi.stockTakes.list({ page_size: 50 }),
    staleTime: 30 * 1000,
  });

  // Fetch selected stock take details
  const { data: selectedTake, isLoading: takeLoading } = useQuery({
    queryKey: ['stock-take', selectedTakeId],
    queryFn: () => selectedTakeId ? stockControlApi.stockTakes.get(selectedTakeId) : null,
    enabled: !!selectedTakeId,
    staleTime: 30 * 1000,
  });

  // Search stock items
  const { data: stockItems } = useQuery({
    queryKey: ['stock-items-search'],
    queryFn: () => getStockItems({ page_size: 100 }),
    staleTime: 5 * 60 * 1000,
  });

  // Create stock take mutation
  const createMutation = useMutation({
    mutationFn: (data: any) => stockControlApi.stockTakes.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-takes'] });
      setActiveTab('list');
    },
  });

  // Complete stock take mutation
  const completeMutation = useMutation({
    mutationFn: (id: number) => stockControlApi.stockTakes.complete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-takes'] });
      queryClient.invalidateQueries({ queryKey: ['stock-take', selectedTakeId] });
    },
  });

  // Update stock mutation
  const updateStockMutation = useMutation({
    mutationFn: (id: number) => stockControlApi.stockTakes.updateStock(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-takes'] });
    },
  });

  // Add + count an item in one step: create the StockTakeItem (capturing the
  // system quantity at this moment) then immediately record the count.
  const addItemMutation = useMutation({
    mutationFn: async () => {
      if (!selectedTakeId || !selectedStockItem) {
        throw new Error('Select a stock item first');
      }
      const item = await stockControlApi.stockTakeItems.create({
        stock_take: selectedTakeId,
        stock_item: selectedStockItem.stock_code,
        quantity_on_hand: selectedStockItem.quantity_on_hand,
        cost_price_at_count: selectedStockItem.cost_price,
      });
      return stockControlApi.stockTakeItems.recordCount(item.id, countForm.quantity_counted);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-take', selectedTakeId] });
      setCountForm({ stock_code: '', quantity_counted: 0 });
      setSelectedStockItem(null);
    },
  });

  const handleSearch = (value: string) => {
    setCountForm(prev => ({ ...prev, stock_code: value }));
    setSelectedStockItem(null);
    if (value.length >= 2 && stockItems) {
      const filtered = stockItems.results.filter((item: any) =>
        item.stock_code.toLowerCase().includes(value.toLowerCase()) ||
        item.description.toLowerCase().includes(value.toLowerCase())
      );
      setSearchResults(filtered.slice(0, 10));
    } else {
      setSearchResults([]);
    }
  };

  const handleCreateTake = () => {
    createMutation.mutate(newTake);
  };

  const handleComplete = () => {
    if (selectedTakeId) {
      completeMutation.mutate(selectedTakeId);
    }
  };

  const handleUpdateStock = () => {
    if (selectedTakeId) {
      updateStockMutation.mutate(selectedTakeId);
    }
  };

  // The backend has no "not yet started" state — a stock take is created
  // directly as IN_PROGRESS, so there is no PENDING bucket to filter for.
  const inProgressTakes = stockTakes?.results?.filter((t: any) => t.status === 'IN_PROGRESS') || [];
  const completedTakes = stockTakes?.results?.filter((t: any) => t.status === 'COMPLETED' || t.status === 'UPDATED') || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/stock-control">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Stock Take</h1>
          <p className="text-gray-600 mt-1">Physical inventory count</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="list">Stock Takes</TabsTrigger>
          <TabsTrigger value="new">New Stock Take</TabsTrigger>
          <TabsTrigger value="count" disabled={!selectedTakeId}>Count Items</TabsTrigger>
        </TabsList>

        {/* List Tab */}
        <TabsContent value="list" className="mt-4">
          {takesLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : (
            <div className="space-y-6">
              {/* In Progress */}
              <Card className="p-6">
                <h3 className="font-semibold mb-4 flex items-center">
                  <Activity className="w-5 h-5 mr-2 text-amber-500" />
                  Newly Created (not yet counted)
                </h3>
                {inProgressTakes.filter((t: any) => !t.item_count).length > 0 ? (
                  <div className="space-y-2">
                    {inProgressTakes.filter((t: any) => !t.item_count).map((take: any) => (
                      <div key={take.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                        <div>
                          <p className="font-medium">Stock Take #{take.id}</p>
                          <p className="text-sm text-gray-500">
                            {take.stock_take_date ? new Date(take.stock_take_date).toLocaleDateString('en-ZA') : 'No date'}
                            {take.description && ` - ${take.description}`}
                          </p>
                        </div>
                        <Button onClick={() => { setSelectedTakeId(take.id); setActiveTab('count'); }} size="sm">
                          Start Counting
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No stock takes waiting to be counted</p>
                )}
              </Card>

              {/* In Progress */}
              <Card className="p-6">
                <h3 className="font-semibold mb-4 flex items-center">
                  <Package className="w-5 h-5 mr-2 text-blue-500" />
                  In Progress
                </h3>
                {inProgressTakes.filter((t: any) => t.item_count).length > 0 ? (
                  <div className="space-y-2">
                    {inProgressTakes.filter((t: any) => t.item_count).map((take: any) => (
                      <div key={take.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                        <div>
                          <p className="font-medium">Stock Take #{take.id}</p>
                          <p className="text-sm text-gray-500">
                            {take.stock_take_date ? new Date(take.stock_take_date).toLocaleDateString('en-ZA') : 'No date'}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button onClick={() => { setSelectedTakeId(take.id); setActiveTab('count'); }} size="sm" variant="outline">
                            Continue
                          </Button>
                          <Button onClick={() => { setSelectedTakeId(take.id); handleComplete(); }} size="sm" className="bg-green-600">
                            Complete
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No stock takes in progress</p>
                )}
              </Card>

              {/* Completed */}
              <Card className="p-6">
                <h3 className="font-semibold mb-4 flex items-center">
                  <CheckCircle className="w-5 h-5 mr-2 text-green-500" />
                  Completed
                </h3>
                {completedTakes.length > 0 ? (
                  <div className="space-y-2">
                    {completedTakes.slice(0, 10).map((take: any) => (
                      <div key={take.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                        <div>
                          <p className="font-medium">Stock Take #{take.id}</p>
                          <p className="text-sm text-gray-500">
                            {take.stock_take_date ? new Date(take.stock_take_date).toLocaleDateString('en-ZA') : 'No date'}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button onClick={() => { setSelectedTakeId(take.id); setActiveTab('count'); }} size="sm" variant="outline">
                            View
                          </Button>
                          <Button onClick={() => { setSelectedTakeId(take.id); handleUpdateStock(); }} size="sm" className="bg-blue-600">
                            Update Stock
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No completed stock takes</p>
                )}
              </Card>
            </div>
          )}
        </TabsContent>

        {/* New Stock Take Tab */}
        <TabsContent value="new" className="mt-4">
          <Card className="p-6">
            <h3 className="font-semibold mb-4">Create New Stock Take</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Stock Take Date</label>
                <Input
                  type="date"
                  value={newTake.stock_take_date}
                  onChange={(e) => setNewTake(prev => ({ ...prev, stock_take_date: e.target.value }))}
                />
              </div>
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-gray-700 mb-1 block">Description</label>
                <Input
                  placeholder="Optional description"
                  value={newTake.description}
                  onChange={(e) => setNewTake(prev => ({ ...prev, description: e.target.value }))}
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end">
              <Button onClick={handleCreateTake} disabled={createMutation.isPending}>
                <Plus className="w-4 h-4 mr-2" />
                {createMutation.isPending ? 'Creating...' : 'Create Stock Take'}
              </Button>
            </div>
          </Card>
        </TabsContent>

        {/* Count Items Tab */}
        <TabsContent value="count" className="mt-4">
          {takeLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : selectedTake ? (
            <div className="space-y-6">
              {/* Take Info */}
              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">Stock Take #{selectedTake.id}</h3>
                    <p className="text-sm text-gray-500">
                      Status: <span className={`px-2 py-0.5 rounded text-xs ${
                        selectedTake.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                        selectedTake.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>{selectedTake.status}</span>
                    </p>
                  </div>
                  {selectedTake.status !== 'COMPLETED' && (
                    <Button onClick={handleComplete} disabled={completeMutation.isPending} className="bg-green-600">
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Complete Stock Take
                    </Button>
                  )}
                </div>
              </Card>

              {/* Add Item Form */}
              {selectedTake.status !== 'COMPLETED' && (
                <Card className="p-6">
                  <h3 className="font-semibold mb-4">Add Item to Count</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="relative">
                      <label className="text-sm font-medium text-gray-700 mb-1 block">Stock Code</label>
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                        <Input
                          placeholder="Search stock code..."
                          value={countForm.stock_code}
                          onChange={(e) => handleSearch(e.target.value)}
                          className="pl-10"
                        />
                      </div>
                      {searchResults.length > 0 && (
                        <div className="absolute z-10 w-full mt-1 border rounded-lg divide-y bg-white shadow-lg max-h-48 overflow-y-auto">
                          {searchResults.map((item: any) => (
                            <button
                              key={item.stock_code}
                              onClick={() => {
                                setCountForm(prev => ({ ...prev, stock_code: item.stock_code }));
                                setSelectedStockItem(item);
                                setSearchResults([]);
                              }}
                              className="w-full px-4 py-2 text-left hover:bg-gray-50"
                            >
                              <span className="font-mono">{item.stock_code}</span>
                              <span className="text-gray-500 ml-2">{item.description}</span>
                            </button>
                          ))}
                        </div>
                      )}
                      {selectedStockItem && (
                        <p className="text-xs text-gray-500 mt-1">
                          System qty on hand: {selectedStockItem.quantity_on_hand}
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-1 block">Counted Quantity</label>
                      <Input
                        type="number"
                        value={countForm.quantity_counted}
                        onChange={(e) => setCountForm(prev => ({ ...prev, quantity_counted: parseFloat(e.target.value) || 0 }))}
                      />
                    </div>
                    <div className="flex items-end">
                      <Button
                        className="w-full"
                        disabled={!selectedStockItem || addItemMutation.isPending}
                        onClick={() => addItemMutation.mutate()}
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        {addItemMutation.isPending ? 'Adding...' : 'Add Item'}
                      </Button>
                    </div>
                  </div>
                  {addItemMutation.isError && (
                    <p className="text-sm text-red-600 mt-2">
                      {(addItemMutation.error as any)?.message || 'Failed to add item'}
                    </p>
                  )}
                </Card>
              )}

              {/* Counted Items */}
              <Card className="p-6">
                <h3 className="font-semibold mb-4">Counted Items</h3>
                {selectedTake.items && selectedTake.items.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="border-b bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium">Stock Code</th>
                          <th className="px-3 py-2 text-left font-medium">Description</th>
                          <th className="px-3 py-2 text-right font-medium">System Qty</th>
                          <th className="px-3 py-2 text-right font-medium">Counted</th>
                          <th className="px-3 py-2 text-right font-medium">Variance</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedTake.items.map((item: any) => (
                          <tr key={item.id} className="border-b hover:bg-gray-50">
                            <td className="px-3 py-2 font-mono">{item.stock_item}</td>
                            <td className="px-3 py-2 text-gray-600">{item.stock_item_detail?.description}</td>
                            <td className="px-3 py-2 text-right">{item.quantity_on_hand}</td>
                            <td className="px-3 py-2 text-right">{item.quantity_counted}</td>
                            <td className={`px-3 py-2 text-right font-medium ${
                              item.variance_quantity > 0 ? 'text-green-600' :
                              item.variance_quantity < 0 ? 'text-red-600' : 'text-gray-500'
                            }`}>
                              {item.variance_quantity}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No items counted yet</p>
                )}
              </Card>
            </div>
          ) : (
            <Card className="p-12 text-center">
              <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 text-lg">Select a stock take to count items</p>
              <Button onClick={() => setActiveTab('list')} className="mt-4">
                Go to Stock Takes
              </Button>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

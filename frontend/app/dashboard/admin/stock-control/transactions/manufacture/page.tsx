'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { getStockItems } from '@/lib/stockApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Loader, ArrowLeft, Plus, Save, Package, 
  Settings, Search, Trash2, Calculator
} from 'lucide-react';
import Link from 'next/link';

export default function ManufacturePage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('list');
  const [showForm, setShowForm] = useState(false);
  const [selectedBundle, setSelectedBundle] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    stock_code: '',
    description: '',
    quantity_produced: 1,
  });
  const [ingredients, setIngredients] = useState<any[]>([]);
  const [newIngredient, setNewIngredient] = useState({
    stock_code: '',
    quantity_required: 0,
  });
  const [searchResults, setSearchResults] = useState<any[]>([]);

  // Fetch pack bundles
  const { data: packBundles, isLoading: bundlesLoading } = useQuery({
    queryKey: ['pack-bundles'],
    queryFn: () => stockControlApi.packBundles.list(),
    staleTime: 30 * 1000,
  });

  // Fetch selected bundle details
  const { data: bundleDetails, isLoading: bundleLoading } = useQuery({
    queryKey: ['pack-bundle', selectedBundle],
    queryFn: () => selectedBundle ? stockControlApi.packBundles.get(selectedBundle) : null,
    enabled: !!selectedBundle,
    staleTime: 30 * 1000,
  });

  // Fetch stock items for ingredient search
  const { data: stockItems } = useQuery({
    queryKey: ['stock-items'],
    queryFn: () => getStockItems({ page_size: 100 }),
    staleTime: 5 * 60 * 1000,
  });

  // Create pack bundle mutation
  const createMutation = useMutation({
    mutationFn: (data: any) => stockControlApi.packBundles.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pack-bundles'] });
      setShowForm(false);
      setIngredients([]);
      setFormData({ stock_code: '', description: '', quantity_produced: 1 });
    },
  });

  // Recalculate cost mutation
  const recalcMutation = useMutation({
    mutationFn: (stockCode: string) => stockControlApi.packBundles.recalculateCost(stockCode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pack-bundle', selectedBundle] });
    },
  });

  const handleSearch = (value: string) => {
    setNewIngredient(prev => ({ ...prev, stock_code: value }));
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

  const addIngredient = () => {
    if (!newIngredient.stock_code || newIngredient.quantity_required <= 0) return;
    setIngredients([...ingredients, { ...newIngredient, id: Date.now() }]);
    setNewIngredient({ stock_code: '', quantity_required: 0 });
    setSearchResults([]);
  };

  const removeIngredient = (id: number) => {
    setIngredients(ingredients.filter(item => item.id !== id));
  };

  const calculateTotalCost = () => {
    return ingredients.reduce((sum, item) => sum + (item.quantity_required * (item.unit_cost || 0)), 0);
  };

  const handleSaveBundle = () => {
    if (!formData.stock_code || ingredients.length === 0) return;
    createMutation.mutate({
      stock_item: formData.stock_code,
      description: formData.description,
      ingredients: ingredients.map(i => ({
        ingredient_stock: i.stock_code,
        quantity_required: i.quantity_required,
      })),
    });
  };

  const handleManufacture = () => {
    // In a real implementation, this would create a manufacture transaction
    // that reduces ingredient stock and increases finished goods stock
    alert('Manufacture transaction would be created via API');
  };

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
          <h1 className="text-3xl font-bold">Manufacture</h1>
          <p className="text-gray-600 mt-1">Pack/bundle manufacturing</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="list">Pack Bundles</TabsTrigger>
          <TabsTrigger value="new">New Bundle</TabsTrigger>
          <TabsTrigger value="manufacture" disabled={!selectedBundle}>Manufacture</TabsTrigger>
        </TabsList>

        {/* List Tab */}
        <TabsContent value="list" className="mt-4">
          {bundlesLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : packBundles?.results && packBundles.results.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {packBundles.results.map((bundle: any) => (
                <Card key={bundle.stock_item} className="p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold font-mono">{bundle.stock_item}</h3>
                      <p className="text-sm text-gray-600 mt-1">{bundle.description || 'No description'}</p>
                    </div>
                    <Package className="w-8 h-8 text-blue-200" />
                  </div>
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-sm text-gray-600">
                      {bundle.ingredients?.length || 0} ingredients
                    </p>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => { setSelectedBundle(bundle.stock_item); setActiveTab('manufacture'); }}
                    >
                      Select
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="p-12 text-center">
              <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 text-lg">No pack bundles defined</p>
              <Button onClick={() => setActiveTab('new')} className="mt-4">
                Create First Bundle
              </Button>
            </Card>
          )}
        </TabsContent>

        {/* New Bundle Tab */}
        <TabsContent value="new" className="mt-4">
          <Card className="p-6">
            <h3 className="font-semibold mb-4">Create New Pack Bundle</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Finished Goods Code</label>
                <Input
                  placeholder="Stock code for finished product"
                  value={formData.stock_code}
                  onChange={(e) => setFormData(prev => ({ ...prev, stock_code: e.target.value }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Description</label>
                <Input
                  placeholder="Bundle description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                />
              </div>
            </div>

            {/* Ingredients */}
            <div className="border rounded-lg p-4 mb-4">
              <h4 className="font-medium mb-3">Ingredients Required</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div className="md:col-span-2 relative">
                  <label className="text-sm font-medium text-gray-700 mb-1 block">Stock Code</label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="Search ingredient..."
                      value={newIngredient.stock_code}
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
                            setNewIngredient(prev => ({ ...prev, stock_code: item.stock_code, unit_cost: item.cost_price || 0 }));
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
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1 block">Qty Required</label>
                  <Input
                    type="number"
                    placeholder="0"
                    value={newIngredient.quantity_required || ''}
                    onChange={(e) => setNewIngredient(prev => ({ ...prev, quantity_required: parseFloat(e.target.value) || 0 }))}
                  />
                </div>
                <div className="flex items-end">
                  <Button onClick={addIngredient} variant="outline" className="w-full">
                    <Plus className="w-4 h-4 mr-2" />
                    Add
                  </Button>
                </div>
              </div>

              {/* Ingredients Table */}
              {ingredients.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left py-2 px-3 font-medium text-gray-600">Stock Code</th>
                        <th className="text-right py-2 px-3 font-medium text-gray-600">Qty Required</th>
                        <th className="text-right py-2 px-3 font-medium text-gray-600">Unit Cost</th>
                        <th className="text-right py-2 px-3 font-medium text-gray-600">Total</th>
                        <th className="text-center py-2 px-3 font-medium text-gray-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ingredients.map((item) => (
                        <tr key={item.id} className="border-b">
                          <td className="py-2 px-3 font-mono">{item.stock_code}</td>
                          <td className="py-2 px-3 text-right">{item.quantity_required}</td>
                          <td className="py-2 px-3 text-right">R {item.unit_cost?.toFixed(2)}</td>
                          <td className="py-2 px-3 text-right font-medium">R {(item.quantity_required * (item.unit_cost || 0)).toFixed(2)}</td>
                          <td className="py-2 px-3 text-center">
                            <Button variant="ghost" size="sm" onClick={() => removeIngredient(item.id)} className="text-red-600">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="font-bold bg-gray-50">
                        <td className="py-2 px-3" colSpan={3}>TOTAL COST</td>
                        <td className="py-2 px-3 text-right">R {calculateTotalCost().toFixed(2)}</td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setActiveTab('list')}>
                Cancel
              </Button>
              <Button onClick={handleSaveBundle} disabled={createMutation.isPending || !formData.stock_code || ingredients.length === 0}>
                <Save className="w-4 h-4 mr-2" />
                {createMutation.isPending ? 'Saving...' : 'Save Bundle'}
              </Button>
            </div>
          </Card>
        </TabsContent>

        {/* Manufacture Tab */}
        <TabsContent value="manufacture" className="mt-4">
          {bundleLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : bundleDetails ? (
            <div className="space-y-6">
              {/* Bundle Info */}
              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-xl">{bundleDetails.stock_item}</h3>
                    <p className="text-gray-600">Pack Bundle</p>
                  </div>
                  <Button 
                    variant="outline" 
                    onClick={() => recalcMutation.mutate(bundleDetails.stock_item)}
                    disabled={recalcMutation.isPending}
                  >
                    <Calculator className="w-4 h-4 mr-2" />
                    Recalculate Cost
                  </Button>
                </div>
              </Card>

              {/* Ingredients Required */}
              <Card className="p-6">
                <h3 className="font-semibold mb-4">Ingredients Required</h3>
                {bundleDetails.ingredients && bundleDetails.ingredients.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b bg-gray-50">
                          <th className="text-left py-2 px-3 font-medium text-gray-600">Ingredient</th>
                          <th className="text-left py-2 px-3 font-medium text-gray-600">Description</th>
                          <th className="text-right py-2 px-3 font-medium text-gray-600">Qty Required</th>
                          <th className="text-right py-2 px-3 font-medium text-gray-600">Available</th>
                          <th className="text-right py-2 px-3 font-medium text-gray-600">Shortage</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bundleDetails.ingredients.map((ing: any, idx: number) => {
                          const available = ing.ingredient_stock_detail?.quantity_on_hand || 0;
                          const shortage = Math.max(0, ing.quantity_required - available);
                          return (
                            <tr key={idx} className="border-b">
                              <td className="py-2 px-3 font-mono">{ing.ingredient_stock}</td>
                              <td className="py-2 px-3">{ing.ingredient_stock_detail?.description || '-'}</td>
                              <td className="py-2 px-3 text-right">{ing.quantity_required}</td>
                              <td className={`py-2 px-3 text-right ${shortage > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                {available.toFixed(2)}
                              </td>
                              <td className={`py-2 px-3 text-right font-medium ${shortage > 0 ? 'text-red-600' : ''}`}>
                                {shortage > 0 ? shortage.toFixed(2) : '-'}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-gray-500">No ingredients defined</p>
                )}
              </Card>

              {/* Manufacture Form */}
              <Card className="p-6">
                <h3 className="font-semibold mb-4">Run Manufacture</h3>
                <div className="flex items-end gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1 block">Quantity to Produce</label>
                    <Input
                      type="number"
                      min="1"
                      value={formData.quantity_produced}
                      onChange={(e) => setFormData(prev => ({ ...prev, quantity_produced: parseInt(e.target.value) || 1 }))}
                      className="w-32"
                    />
                  </div>
                  <Button onClick={handleManufacture}>
                    <Settings className="w-4 h-4 mr-2" />
                    Manufacture
                  </Button>
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  This will reduce ingredient stock and increase finished goods stock
                </p>
              </Card>
            </div>
          ) : (
            <Card className="p-12 text-center">
              <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 text-lg">Select a pack bundle to manufacture</p>
              <Button onClick={() => setActiveTab('list')} className="mt-4">
                Go to Pack Bundles
              </Button>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

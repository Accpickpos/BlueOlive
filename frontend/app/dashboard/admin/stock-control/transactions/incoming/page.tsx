'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { getStockItems } from '@/lib/stockApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { 
  Loader, ArrowLeft, Plus, Save, Package, 
  ArrowDown, Search, Trash2
} from 'lucide-react';
import Link from 'next/link';

export default function IncomingStockPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    reference: '',
    supplier: '',
    date_received: new Date().toISOString().split('T')[0],
    notes: '',
  });
  const [lineItems, setLineItems] = useState<any[]>([]);
  const [newItem, setNewItem] = useState({
    stock_code: '',
    quantity: 0,
    unit_cost: 0,
  });
  const [searchResults, setSearchResults] = useState<any[]>([]);

  // Fetch stock items
  const { data: stockItems } = useQuery({
    queryKey: ['stock-items'],
    queryFn: () => getStockItems({ page_size: 100 }),
    staleTime: 5 * 60 * 1000,
  });

  // Search stock items
  const handleSearch = (value: string) => {
    setNewItem(prev => ({ ...prev, stock_code: value }));
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

  const addLineItem = () => {
    if (!newItem.stock_code || newItem.quantity <= 0) return;
    setLineItems([...lineItems, { ...newItem, id: Date.now() }]);
    setNewItem({ stock_code: '', quantity: 0, unit_cost: 0 });
    setSearchResults([]);
  };

  const removeLineItem = (id: number) => {
    setLineItems(lineItems.filter(item => item.id !== id));
  };

  const totalValue = lineItems.reduce((sum, item) => sum + (item.quantity * item.unit_cost), 0);

  const handleSave = () => {
    // In a real implementation, this would call the API to create a stock transaction
    alert('Stock incoming transaction would be created via API');
    setShowForm(false);
    setLineItems([]);
    setFormData({ reference: '', supplier: '', date_received: new Date().toISOString().split('T')[0], notes: '' });
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
          <h1 className="text-3xl font-bold">Incoming Stock</h1>
          <p className="text-gray-600 mt-1">Goods received notes</p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end">
        {!showForm && (
          <Button onClick={() => setShowForm(true)}>
            <Plus className="w-4 h-4 mr-2" />
            New Stock Receipt
          </Button>
        )}
      </div>

      {/* Form */}
      {showForm && (
        <Card className="p-6">
          <h3 className="font-semibold mb-4">New Stock Receipt</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Reference</label>
              <Input
                placeholder="GRN/PO Reference"
                value={formData.reference}
                onChange={(e) => setFormData(prev => ({ ...prev, reference: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Date Received</label>
              <Input
                type="date"
                value={formData.date_received}
                onChange={(e) => setFormData(prev => ({ ...prev, date_received: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Notes</label>
              <Input
                placeholder="Optional notes"
                value={formData.notes}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
              />
            </div>
          </div>

          {/* Line Items */}
          <div className="border rounded-lg p-4 mb-4">
            <h4 className="font-medium mb-3">Line Items</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div className="relative">
                <label className="text-sm font-medium text-gray-700 mb-1 block">Stock Code</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Search stock code..."
                    value={newItem.stock_code}
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
                          setNewItem(prev => ({ ...prev, stock_code: item.stock_code, unit_cost: item.cost_price || 0 }));
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
                <label className="text-sm font-medium text-gray-700 mb-1 block">Quantity</label>
                <Input
                  type="number"
                  placeholder="0"
                  value={newItem.quantity || ''}
                  onChange={(e) => setNewItem(prev => ({ ...prev, quantity: parseFloat(e.target.value) || 0 }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Unit Cost</label>
                <Input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={newItem.unit_cost || ''}
                  onChange={(e) => setNewItem(prev => ({ ...prev, unit_cost: parseFloat(e.target.value) || 0 }))}
                />
              </div>
              <div className="flex items-end">
                <Button onClick={addLineItem} variant="outline" className="w-full">
                  <Plus className="w-4 h-4 mr-2" />
                  Add
                </Button>
              </div>
            </div>

            {/* Items Table */}
            {lineItems.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-gray-50">
                      <th className="text-left py-2 px-3 font-medium text-gray-600">Stock Code</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">Quantity</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">Unit Cost</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">Total</th>
                      <th className="text-center py-2 px-3 font-medium text-gray-600">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lineItems.map((item) => (
                      <tr key={item.id} className="border-b">
                        <td className="py-2 px-3 font-mono">{item.stock_code}</td>
                        <td className="py-2 px-3 text-right">{item.quantity}</td>
                        <td className="py-2 px-3 text-right">R {item.unit_cost?.toFixed(2)}</td>
                        <td className="py-2 px-3 text-right font-medium">R {(item.quantity * item.unit_cost).toFixed(2)}</td>
                        <td className="py-2 px-3 text-center">
                          <Button variant="ghost" size="sm" onClick={() => removeLineItem(item.id)} className="text-red-600">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="font-bold bg-gray-50">
                      <td className="py-2 px-3" colSpan={3}>TOTAL</td>
                      <td className="py-2 px-3 text-right">R {totalValue.toFixed(2)}</td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowForm(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={lineItems.length === 0}>
              <Save className="w-4 h-4 mr-2" />
              Save Receipt
            </Button>
          </div>
        </Card>
      )}

      {/* Recent Receipts Placeholder */}
      {!showForm && (
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Recent Stock Receipts</h3>
          <div className="text-center py-12">
            <ArrowDown className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">Stock incoming receipts would be listed here</p>
            <p className="text-gray-500 text-sm mt-1">Connect to stock transactions API for full functionality</p>
          </div>
        </Card>
      )}
    </div>
  );
}

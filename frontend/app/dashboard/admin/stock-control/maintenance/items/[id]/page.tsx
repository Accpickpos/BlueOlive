'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getStockItem, createStockItem, updateStockItem } from '@/lib/stockApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader, Save } from 'lucide-react';

export default function StockItemFormPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const isNew = params.id === 'new';

  const [formData, setFormData] = useState({
    stock_code: '', description: '', department: '', supplier: '',
    supplier_code: '', tax_code: 1, reorder_quantity: 0,
    cost_price: 0, allow_negative_quantities: false,
    default_selling_quantity: 1, automatic_returns: false,
    maximum_discount_percent: 0,
    markup_1: 0, markup_2: 0, markup_3: 0,
    selling_price_1: 0, selling_price_2: 0, selling_price_3: 0,
  });

  const [quantities, setQuantities] = useState({
    quantity_on_hand: 0, quantity_allocated: 0, quantity_sale_order: 0,
  });

  const { data: existingItem, isLoading } = useQuery({
    queryKey: ['stock-item', params.id],
    queryFn: () => getStockItem(String(params.id)),
    enabled: !isNew,
  });

  useEffect(() => {
    if (existingItem) {
      const updated: any = { ...existingItem };
      setFormData(updated);
      setQuantities({
        quantity_on_hand: (existingItem as any)?.quantity_on_hand || 0,
        quantity_allocated: (existingItem as any)?.quantity_allocated || 0,
        quantity_sale_order: (existingItem as any)?.quantity_sale_order || 0,
      });
    }
  }, [existingItem]);

  const handleMarkupChange = (field: string, value: number) => {
    const markup = parseFloat(value.toString()) || 0;
    const cost = parseFloat(formData.cost_price.toString()) || 0;
    const sellingPrice = cost * (1 + markup / 100);
    setFormData(prev => ({
      ...prev,
      [field]: markup,
      [field.replace('markup', 'selling_price')]: sellingPrice,
    }));
  };

  const mutation = useMutation({
    mutationFn: (data: typeof formData) => {
      if (isNew) return createStockItem(data);
      return updateStockItem(String(params.id), data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-items'] });
      router.push('/dashboard/admin/stock-control/maintenance/items');
    },
  });

  if (!isNew && isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            {isNew ? 'New Stock Item' : `Edit Stock Item: ${params.id}`}
          </h1>
          <p className="text-gray-600 mt-1">
            {isNew ? 'Create a new stock item' : 'Modify stock item details'}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.back()}>Cancel</Button>
          <Button className="bg-green-600 hover:bg-green-700" onClick={() => mutation.mutate(formData)} disabled={mutation.isPending}>
            <Save className="w-4 h-4 mr-2" />
            {mutation.isPending ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </div>

      {isNew && (
        <Card className="p-6">
          <h2 className="text-lg font-bold mb-4">Stock Code</h2>
          <div>
            <label className="text-sm font-medium">Stock Code</label>
            <Input
              value={formData.stock_code}
              onChange={(e) => setFormData(prev => ({ ...prev, stock_code: e.target.value }))}
              placeholder="Enter 1-13 alphanumeric code"
              maxLength={13}
              required
            />
          </div>
        </Card>
      )}

      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Item Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium">Item Description</label>
            <Input
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium">Department</label>
            <Select value={formData.department?.toString()} onValueChange={(value: string) => setFormData(prev => ({ ...prev, department: value }))}>
              <SelectTrigger>
                <SelectValue placeholder="Select Department" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Select Department</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium">Tax Code</label>
            <Select value={formData.tax_code?.toString()} onValueChange={(value: string) => setFormData(prev => ({ ...prev, tax_code: parseInt(value) }))}>
              <SelectTrigger>
                <SelectValue placeholder="Select Tax Code" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1 - 15% VAT</SelectItem>
                <SelectItem value="2">2 - 0% VAT</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium">Supplier</label>
            <Select value={formData.supplier?.toString()} onValueChange={(value: string) => setFormData(prev => ({ ...prev, supplier: value }))}>
              <SelectTrigger>
                <SelectValue placeholder="Select Supplier" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Select Supplier</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium">Supplier Code</label>
            <Input value={formData.supplier_code || ''} onChange={(e) => setFormData(prev => ({ ...prev, supplier_code: e.target.value }))} />
          </div>
          <div>
            <label className="text-sm font-medium">Re-order Quantity</label>
            <Input type="number" value={formData.reorder_quantity} onChange={(e) => setFormData(prev => ({ ...prev, reorder_quantity: parseFloat(e.target.value) || 0 }))} />
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Quantities</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm font-medium">Quantity on Hand</label>
            <Input type="number" value={quantities.quantity_on_hand} onChange={(e) => setQuantities(prev => ({ ...prev, quantity_on_hand: parseFloat(e.target.value) || 0 }))} />
          </div>
          <div>
            <label className="text-sm font-medium">Quantity Allocated</label>
            <Input type="number" value={quantities.quantity_allocated} onChange={(e) => setQuantities(prev => ({ ...prev, quantity_allocated: parseFloat(e.target.value) || 0 }))} />
          </div>
          <div>
            <label className="text-sm font-medium">Quantity on Sales Order</label>
            <Input type="number" value={quantities.quantity_sale_order} onChange={(e) => setQuantities(prev => ({ ...prev, quantity_sale_order: parseFloat(e.target.value) || 0 }))} />
          </div>
        </div>
        <div className="mt-4 p-4 bg-gray-100 rounded">
          <p className="font-bold">Available Quantity: {Math.max(0, quantities.quantity_on_hand - quantities.quantity_allocated - quantities.quantity_sale_order).toFixed(2)}</p>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Pricing</h2>
        <Tabs defaultValue="price1">
          <TabsList>
            <TabsTrigger value="price1">Price Level 1</TabsTrigger>
            <TabsTrigger value="price2">Price Level 2</TabsTrigger>
            <TabsTrigger value="price3">Price Level 3</TabsTrigger>
          </TabsList>

          <TabsContent value="price1" className="mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Cost Price</label>
                <Input type="number" value={formData.cost_price} onChange={(e) => setFormData(prev => ({ ...prev, cost_price: parseFloat(e.target.value) || 0 }))} />
              </div>
              <div>
                <label className="text-sm font-medium">Markup %</label>
                <Input type="number" value={formData.markup_1} onChange={(e) => handleMarkupChange('markup_1', parseFloat(e.target.value) || 0)} />
              </div>
              <div>
                <label className="text-sm font-medium">Selling Price 1</label>
                <Input type="number" value={formData.selling_price_1} onChange={(e) => {
                  const sp = parseFloat(e.target.value) || 0;
                  const cost = parseFloat(formData.cost_price.toString()) || 0;
                  const markup = cost > 0 ? ((sp - cost) / cost) * 100 : 0;
                  setFormData(prev => ({ ...prev, markup_1: markup, selling_price_1: sp }));
                }} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="price2" className="mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Markup %</label>
                <Input type="number" value={formData.markup_2} onChange={(e) => handleMarkupChange('markup_2', parseFloat(e.target.value) || 0)} />
              </div>
              <div>
                <label className="text-sm font-medium">Selling Price 2</label>
                <Input type="number" value={formData.selling_price_2} onChange={(e) => {
                  const sp = parseFloat(e.target.value) || 0;
                  const cost = parseFloat(formData.cost_price.toString()) || 0;
                  const markup = cost > 0 ? ((sp - cost) / cost) * 100 : 0;
                  setFormData(prev => ({ ...prev, markup_2: markup, selling_price_2: sp }));
                }} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="price3" className="mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Markup %</label>
                <Input type="number" value={formData.markup_3} onChange={(e) => handleMarkupChange('markup_3', parseFloat(e.target.value) || 0)} />
              </div>
              <div>
                <label className="text-sm font-medium">Selling Price 3</label>
                <Input type="number" value={formData.selling_price_3} onChange={(e) => {
                  const sp = parseFloat(e.target.value) || 0;
                  const cost = parseFloat(formData.cost_price.toString()) || 0;
                  const markup = cost > 0 ? ((sp - cost) / cost) * 100 : 0;
                  setFormData(prev => ({ ...prev, markup_3: markup, selling_price_3: sp }));
                }} />
              </div>
            </div>
          </TabsContent>
        </Tabs>
        <div className="mt-4">
          <label className="text-sm font-medium">Maximum Discount %</label>
          <Input type="number" value={formData.maximum_discount_percent} onChange={(e) => setFormData(prev => ({ ...prev, maximum_discount_percent: parseFloat(e.target.value) || 0 }))} />
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">Options</h2>
        <div className="space-y-4">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={formData.allow_negative_quantities} onChange={(e) => setFormData(prev => ({ ...prev, allow_negative_quantities: e.target.checked }))} />
            <span>Allow Negative Quantities</span>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={formData.automatic_returns} onChange={(e) => setFormData(prev => ({ ...prev, automatic_returns: e.target.checked }))} />
            <span>Automatic Returns (e.g., empty bottles)</span>
          </label>
        </div>
      </Card>
    </div>
  );
}

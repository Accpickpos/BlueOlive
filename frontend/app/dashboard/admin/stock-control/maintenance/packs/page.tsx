'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Plus, Pencil, Trash2, Search, Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

interface PackBundle {
  id: number;
  stock_code: string;
  description?: string;
  pack_quantity: number;
  is_active: boolean;
  ingredients_count?: number;
}

export default function PacksPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isIngredientsOpen, setIsIngredientsOpen] = useState(false);
  const [editingPack, setEditingPack] = useState<PackBundle | null>(null);
  const [selectedPack, setSelectedPack] = useState<PackBundle | null>(null);
  const [formData, setFormData] = useState({
    stock_code: '',
    description: '',
    pack_quantity: 1,
    is_active: true,
  });
  const [newIngredient, setNewIngredient] = useState({
    ingredient_stock: '',
    quantity_required: 1,
  });
  const [ingredients, setIngredients] = useState<any[]>([]);

  const { data: packs, isLoading } = useQuery({
    queryKey: ['pack-bundles'],
    queryFn: () => apiRequest('/api/v1/stock-control/pack-bundles/'),
    select: (response) => response.data.results || response.data,
  });

  const { data: stockItems } = useQuery({
    queryKey: ['stock-items'],
    queryFn: () => apiRequest('/api/v1/stock-control/stock-items/'),
    select: (response) => response.data.results || response.data,
  });

  const { data: ingredientsData } = useQuery({
    queryKey: ['pack-bundle-ingredients', selectedPack?.id],
    queryFn: () => apiRequest(`/api/v1/stock-control/pack-bundle-ingredients/?pack_bundle=${selectedPack?.id}`),
    enabled: !!selectedPack,
    select: (response) => response.data.results || response.data,
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      apiRequest('/api/v1/stock-control/pack-bundles/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pack-bundles'] });
      setIsDialogOpen(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: typeof formData }) =>
      apiRequest(`/api/v1/stock-control/pack-bundles/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pack-bundles'] });
      setIsDialogOpen(false);
      setEditingPack(null);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiRequest(`/api/v1/stock-control/pack-bundles/${id}/`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pack-bundles'] });
    },
  });

  const addIngredientMutation = useMutation({
    mutationFn: (data: any) =>
      apiRequest('/api/v1/stock-control/pack-bundle-ingredients/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pack-bundle-ingredients', selectedPack?.id] });
      setNewIngredient({ ingredient_stock: '', quantity_required: 1 });
    },
  });

  const deleteIngredientMutation = useMutation({
    mutationFn: (id: number) =>
      apiRequest(`/api/v1/stock-control/pack-bundle-ingredients/${id}/`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pack-bundle-ingredients', selectedPack?.id] });
    },
  });

  const resetForm = () => {
    setFormData({
      stock_code: '',
      description: '',
      pack_quantity: 1,
      is_active: true,
    });
    setIngredients([]);
  };

  const handleEdit = (pack: PackBundle) => {
    setEditingPack(pack);
    setFormData({
      stock_code: pack.stock_code,
      description: pack.description || '',
      pack_quantity: pack.pack_quantity,
      is_active: pack.is_active,
    });
    setIsDialogOpen(true);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this pack bundle?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleManageIngredients = (pack: PackBundle) => {
    setSelectedPack(pack);
    setIsIngredientsOpen(true);
  };

  const handleAddIngredient = () => {
    if (!selectedPack || !newIngredient.ingredient_stock) return;
    addIngredientMutation.mutate({
      pack_bundle: selectedPack.id,
      ingredient_stock: newIngredient.ingredient_stock,
      quantity_required: newIngredient.quantity_required,
    });
  };

  const handleSubmit = () => {
    if (editingPack) {
      updateMutation.mutate({ id: editingPack.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const filteredPacks = packs?.filter((pack: PackBundle) =>
    pack.stock_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    pack.description?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/stock-control">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Packs/Bundles</h1>
          <p className="text-gray-600 mt-1">Manage finished goods and recipes</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by pack code or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            onClick={() => {
              resetForm();
              setEditingPack(null);
              setIsDialogOpen(true);
            }}
            className="ml-4"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Pack/Bundle
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading packs/bundles...</p>
          </div>
        ) : filteredPacks.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No packs/bundles found. Click "Add Pack/Bundle" to create one.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Pack Code</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Pack Quantity</TableHead>
                <TableHead>Ingredients</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPacks.map((pack: PackBundle) => (
                <TableRow key={pack.id}>
                  <TableCell className="font-medium">{pack.stock_code}</TableCell>
                  <TableCell>{pack.description || '-'}</TableCell>
                  <TableCell>{pack.pack_quantity}</TableCell>
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleManageIngredients(pack)}
                    >
                      Manage ({pack.ingredients_count || 0})
                    </Button>
                  </TableCell>
                  <TableCell>
                    <Badge variant={pack.is_active ? 'default' : 'secondary'}>
                      {pack.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(pack)}>
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(pack.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingPack ? 'Edit Pack/Bundle' : 'Add Pack/Bundle'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Pack Code</label>
              <Select
                value={formData.stock_code}
                onValueChange={(value) => setFormData({ ...formData, stock_code: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select stock item" />
                </SelectTrigger>
                <SelectContent>
                  {stockItems?.map((item: any) => (
                    <SelectItem key={item.stock_code} value={item.stock_code}>
                      {item.stock_code} - {item.description}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Pack description"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Pack Quantity</label>
              <Input
                type="number"
                value={formData.pack_quantity}
                onChange={(e) =>
                  setFormData({ ...formData, pack_quantity: parseInt(e.target.value) || 1 })
                }
                placeholder="e.g., 6"
              />
              <p className="text-xs text-gray-500 mt-1">Number of units in this pack</p>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="w-4 h-4"
              />
              <label htmlFor="is_active" className="text-sm font-medium">
                Active
              </label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {createMutation.isPending || updateMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : null}
              {editingPack ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Ingredients Dialog */}
      <Dialog open={isIngredientsOpen} onOpenChange={setIsIngredientsOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              Manage Ingredients for {selectedPack?.stock_code}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <Select
                  value={newIngredient.ingredient_stock}
                  onValueChange={(value) =>
                    setNewIngredient({ ...newIngredient, ingredient_stock: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select ingredient" />
                  </SelectTrigger>
                  <SelectContent>
                    {stockItems?.map((item: any) => (
                      <SelectItem key={item.stock_code} value={item.stock_code}>
                        {item.stock_code} - {item.description}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Input
                type="number"
                className="w-24"
                value={newIngredient.quantity_required}
                onChange={(e) =>
                  setNewIngredient({
                    ...newIngredient,
                    quantity_required: parseInt(e.target.value) || 1,
                  })
                }
                placeholder="Qty"
              />
              <Button onClick={handleAddIngredient} disabled={addIngredientMutation.isPending}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ingredient Code</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Quantity Required</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ingredientsData?.map((ing: any) => (
                  <TableRow key={ing.id}>
                    <TableCell>{ing.ingredient_stock}</TableCell>
                    <TableCell>{ing.ingredient_stock_description || '-'}</TableCell>
                    <TableCell>{ing.quantity_required}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteIngredientMutation.mutate(ing.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

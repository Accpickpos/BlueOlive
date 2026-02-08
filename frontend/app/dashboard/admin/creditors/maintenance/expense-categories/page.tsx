'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { creditorsApi } from '@/lib/creditorsApi';
import type { ExpenseCategory } from '@/lib/types/creditors';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader, Plus, Edit, Trash2 } from 'lucide-react';

export default function ExpenseCategoriesPage() {
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<Partial<ExpenseCategory>>({
    category_number: '',
    name: '',
  });

  const { data: categories, isLoading } = useQuery({
    queryKey: ['expense-categories'],
    queryFn: () => creditorsApi.expenseCategories.list({ page_size: 100 }),
  });

  const addMutation = useMutation({
    mutationFn: (data: Partial<ExpenseCategory>) => creditorsApi.expenseCategories.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-categories'] });
      setFormData({ category_number: '', name: '' });
      setIsAdding(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<ExpenseCategory>) =>
      creditorsApi.expenseCategories.update(editingId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-categories'] });
      setFormData({ category_number: '', name: '' });
      setEditingId(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => creditorsApi.expenseCategories.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expense-categories'] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId) {
      updateMutation.mutate(formData);
    } else {
      addMutation.mutate(formData);
    }
  };

  const handleEdit = (category: ExpenseCategory) => {
    setEditingId(category.id);
    setFormData(category);
  };

  const handleCancel = () => {
    setIsAdding(false);
    setEditingId(null);
    setFormData({ category_number: '', name: '' });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Expense Categories</h1>
          <p className="text-gray-600 mt-1">Manage expense categories for creditor transactions</p>
        </div>
        <Button
          className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2"
          onClick={() => setIsAdding(true)}
          disabled={isAdding || editingId !== null}
        >
          <Plus className="w-4 h-4" />
          New Category
        </Button>
      </div>

      {/* Add/Edit Form */}
      {(isAdding || editingId !== null) && (
        <Card className="p-6 bg-blue-50 border-blue-200">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Category Number</label>
                <Input
                  type="text"
                  value={formData.category_number || ''}
                  onChange={(e) => setFormData({ ...formData, category_number: e.target.value })}
                  placeholder="1-8 digits"
                  required
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Category Name</label>
                <Input
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Office Supplies, Fuel, Repairs"
                  required
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                type="submit"
                className="bg-green-600 hover:bg-green-700"
                disabled={addMutation.isPending || updateMutation.isPending}
              >
                {editingId ? 'Update Category' : 'Add Category'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Categories Table */}
      <Card className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Category #</th>
                <th className="px-4 py-3 text-left font-semibold">Name</th>
                <th className="px-4 py-3 text-center font-semibold">Transactions</th>
                <th className="px-4 py-3 text-center font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {categories?.results?.map((category: ExpenseCategory) => (
                <tr key={category.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{category.category_number}</td>
                  <td className="px-4 py-3">{category.name}</td>
                  <td className="px-4 py-3 text-center text-gray-600">{category.transaction_count || 0}</td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="w-8 h-8 p-0"
                        onClick={() => handleEdit(category)}
                        disabled={isAdding || editingId !== null}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        className="w-8 h-8 p-0"
                        onClick={() => {
                          if ((category.transaction_count || 0) > 0) {
                            alert('Cannot delete - expenses have been recorded in this category');
                            return;
                          }
                          if (confirm('Are you sure you want to delete this category?')) {
                            deleteMutation.mutate(category.id);
                          }
                        }}
                        disabled={editingId !== null}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {(!categories?.results || categories.results.length === 0) && (
          <div className="text-center py-8 text-gray-500">
            No expense categories found. Click "New Category" to create one.
          </div>
        )}
      </Card>
    </div>
  );
}

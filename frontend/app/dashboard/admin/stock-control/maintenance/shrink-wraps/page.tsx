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

interface ShrinkWrap {
  id: number;
  shrink_pack_code: string;
  shrink_pack_description?: string;
  bulk_pack_code: string;
  bulk_pack_description?: string;
  conversion_factor: number;
  is_active: boolean;
}

export default function ShrinkWrapsPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<ShrinkWrap | null>(null);
  const [formData, setFormData] = useState({
    shrink_pack_code: '',
    bulk_pack_code: '',
    conversion_factor: 1,
    is_active: true,
  });

  const { data: items, isLoading } = useQuery({
    queryKey: ['shrink-wraps'],
    queryFn: () => apiRequest('/api/v1/stock-control/shrink-wraps/'),
    select: (response) => response.data.results || response.data,
  });

  const { data: stockItems } = useQuery({
    queryKey: ['stock-items'],
    queryFn: () => apiRequest('/api/v1/stock-control/stock-items/'),
    select: (response) => response.data.results || response.data,
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      apiRequest('/api/v1/stock-control/shrink-wraps/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shrink-wraps'] });
      setIsDialogOpen(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: typeof formData }) =>
      apiRequest(`/api/v1/stock-control/shrink-wraps/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shrink-wraps'] });
      setIsDialogOpen(false);
      setEditingItem(null);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiRequest(`/api/v1/stock-control/shrink-wraps/${id}/`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shrink-wraps'] });
    },
  });

  const resetForm = () => {
    setFormData({
      shrink_pack_code: '',
      bulk_pack_code: '',
      conversion_factor: 1,
      is_active: true,
    });
  };

  const handleEdit = (item: ShrinkWrap) => {
    setEditingItem(item);
    setFormData({
      shrink_pack_code: item.shrink_pack_code,
      bulk_pack_code: item.bulk_pack_code,
      conversion_factor: item.conversion_factor,
      is_active: item.is_active,
    });
    setIsDialogOpen(true);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this shrink wrap relationship?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleSubmit = () => {
    if (editingItem) {
      updateMutation.mutate({ id: editingItem.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const filteredItems = items?.filter((item: ShrinkWrap) =>
    item.shrink_pack_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.bulk_pack_code?.toLowerCase().includes(searchTerm.toLowerCase())
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
          <h1 className="text-3xl font-bold">Shrink Wraps</h1>
          <p className="text-gray-600 mt-1">Manage bulk to unit relationships</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by pack code..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            onClick={() => {
              resetForm();
              setEditingItem(null);
              setIsDialogOpen(true);
            }}
            className="ml-4"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Shrink Wrap
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading shrink wraps...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No shrink wrap relationships found. Click "Add Shrink Wrap" to create one.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Shrink Pack Code</TableHead>
                <TableHead>Shrink Pack Description</TableHead>
                <TableHead>Bulk Pack Code</TableHead>
                <TableHead>Bulk Pack Description</TableHead>
                <TableHead>Conversion Factor</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredItems.map((item: ShrinkWrap) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.shrink_pack_code}</TableCell>
                  <TableCell>{item.shrink_pack_description || '-'}</TableCell>
                  <TableCell>{item.bulk_pack_code}</TableCell>
                  <TableCell>{item.bulk_pack_description || '-'}</TableCell>
                  <TableCell>{item.conversion_factor}</TableCell>
                  <TableCell>
                    <Badge variant={item.is_active ? 'default' : 'secondary'}>
                      {item.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(item)}>
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(item.id)}
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

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingItem ? 'Edit Shrink Wrap' : 'Add Shrink Wrap'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Shrink Pack (Unit)</label>
              <Select
                value={formData.shrink_pack_code}
                onValueChange={(value) => setFormData({ ...formData, shrink_pack_code: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select shrink pack" />
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
              <label className="text-sm font-medium">Bulk Pack</label>
              <Select
                value={formData.bulk_pack_code}
                onValueChange={(value) => setFormData({ ...formData, bulk_pack_code: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select bulk pack" />
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
              <label className="text-sm font-medium">Conversion Factor</label>
              <Input
                type="number"
                value={formData.conversion_factor}
                onChange={(e) =>
                  setFormData({ ...formData, conversion_factor: parseInt(e.target.value) || 1 })
                }
                placeholder="e.g., 12"
              />
              <p className="text-xs text-gray-500 mt-1">Number of units per bulk pack</p>
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
              {editingItem ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

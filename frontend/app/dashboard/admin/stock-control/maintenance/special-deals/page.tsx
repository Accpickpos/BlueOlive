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

interface SpecialDeal {
  id: number;
  stock_item: string;
  stock_item_description?: string;
  discount_percent: number;
  deal_start_date: string;
  deal_end_date: string;
  is_active: boolean;
}

export default function SpecialDealsPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingDeal, setEditingDeal] = useState<SpecialDeal | null>(null);
  const [formData, setFormData] = useState({
    stock_item: '',
    discount_percent: 0,
    deal_start_date: '',
    deal_end_date: '',
    is_active: true,
  });

  const { data: deals, isLoading } = useQuery({
    queryKey: ['special-deals'],
    queryFn: () => apiRequest('/api/v1/stock-control/special-deals/'),
    select: (response) => response.data.results || response.data,
  });

  const { data: stockItems } = useQuery({
    queryKey: ['stock-items'],
    queryFn: () => apiRequest('/api/v1/stock-control/stock-items/'),
    select: (response) => response.data.results || response.data,
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      apiRequest('/api/v1/stock-control/special-deals/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['special-deals'] });
      setIsDialogOpen(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: typeof formData }) =>
      apiRequest(`/api/v1/stock-control/special-deals/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['special-deals'] });
      setIsDialogOpen(false);
      setEditingDeal(null);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiRequest(`/api/v1/stock-control/special-deals/${id}/`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['special-deals'] });
    },
  });

  const resetForm = () => {
    setFormData({
      stock_item: '',
      discount_percent: 0,
      deal_start_date: '',
      deal_end_date: '',
      is_active: true,
    });
  };

  const handleEdit = (deal: SpecialDeal) => {
    setEditingDeal(deal);
    setFormData({
      stock_item: deal.stock_item,
      discount_percent: deal.discount_percent,
      deal_start_date: deal.deal_start_date,
      deal_end_date: deal.deal_end_date,
      is_active: deal.is_active,
    });
    setIsDialogOpen(true);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this special deal?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleSubmit = () => {
    if (editingDeal) {
      updateMutation.mutate({ id: editingDeal.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const filteredDeals = deals?.filter((deal: SpecialDeal) =>
    deal.stock_item?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    deal.stock_item_description?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

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
          <h1 className="text-3xl font-bold">Special Deals</h1>
          <p className="text-gray-600 mt-1">Manage promotional pricing and special offers</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by stock code or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            onClick={() => {
              resetForm();
              setEditingDeal(null);
              setIsDialogOpen(true);
            }}
            className="ml-4"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Special Deal
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading special deals...</p>
          </div>
        ) : filteredDeals.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No special deals found. Click "Add Special Deal" to create one.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Stock Code</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Discount %</TableHead>
                <TableHead>Start Date</TableHead>
                <TableHead>End Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDeals.map((deal: SpecialDeal) => (
                <TableRow key={deal.id}>
                  <TableCell className="font-medium">{deal.stock_item}</TableCell>
                  <TableCell>{deal.stock_item_description || '-'}</TableCell>
                  <TableCell>{deal.discount_percent}%</TableCell>
                  <TableCell>{formatDate(deal.deal_start_date)}</TableCell>
                  <TableCell>{formatDate(deal.deal_end_date)}</TableCell>
                  <TableCell>
                    <Badge variant={deal.is_active ? 'default' : 'secondary'}>
                      {deal.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(deal)}
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(deal.id)}
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
              {editingDeal ? 'Edit Special Deal' : 'Add Special Deal'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Stock Item</label>
              <Select
                value={formData.stock_item}
                onValueChange={(value) => setFormData({ ...formData, stock_item: value })}
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
              <label className="text-sm font-medium">Discount Percent</label>
              <Input
                type="number"
                step="0.01"
                value={formData.discount_percent}
                onChange={(e) =>
                  setFormData({ ...formData, discount_percent: parseFloat(e.target.value) || 0 })
                }
                placeholder="e.g., 10.00"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Start Date</label>
              <Input
                type="date"
                value={formData.deal_start_date}
                onChange={(e) => setFormData({ ...formData, deal_start_date: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm font-medium">End Date</label>
              <Input
                type="date"
                value={formData.deal_end_date}
                onChange={(e) => setFormData({ ...formData, deal_end_date: e.target.value })}
              />
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
              {editingDeal ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

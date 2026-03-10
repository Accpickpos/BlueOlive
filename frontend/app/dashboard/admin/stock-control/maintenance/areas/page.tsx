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
import { Plus, Pencil, Trash2, Search, Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

interface SalesArea {
  id: number;
  area_code: string;
  area_name: string;
  is_active: boolean;
}

export default function AreasPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingArea, setEditingArea] = useState<SalesArea | null>(null);
  const [formData, setFormData] = useState({
    area_code: '',
    area_name: '',
    is_active: true,
  });

  const { data: areas, isLoading } = useQuery({
    queryKey: ['sales-areas'],
    queryFn: () => apiRequest('/api/v1/settings/sales-areas/'),
    select: (response) => response.data.results || response.data,
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      apiRequest('/api/v1/settings/sales-areas/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sales-areas'] });
      setIsDialogOpen(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: typeof formData }) =>
      apiRequest(`/api/v1/settings/sales-areas/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sales-areas'] });
      setIsDialogOpen(false);
      setEditingArea(null);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiRequest(`/api/v1/settings/sales-areas/${id}/`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sales-areas'] });
    },
  });

  const resetForm = () => {
    setFormData({
      area_code: '',
      area_name: '',
      is_active: true,
    });
  };

  const handleEdit = (area: SalesArea) => {
    setEditingArea(area);
    setFormData({
      area_code: area.area_code,
      area_name: area.area_name,
      is_active: area.is_active,
    });
    setIsDialogOpen(true);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this sales area?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleSubmit = () => {
    if (editingArea) {
      updateMutation.mutate({ id: editingArea.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const filteredAreas = areas?.filter((area: SalesArea) =>
    area.area_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    area.area_name?.toLowerCase().includes(searchTerm.toLowerCase())
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
          <h1 className="text-3xl font-bold">Sales Areas</h1>
          <p className="text-gray-600 mt-1">Salesman and area management</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by code or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            onClick={() => {
              resetForm();
              setEditingArea(null);
              setIsDialogOpen(true);
            }}
            className="ml-4"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Sales Area
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading sales areas...</p>
          </div>
        ) : filteredAreas.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No sales areas found. Click "Add Sales Area" to create one.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Area Code</TableHead>
                <TableHead>Area Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAreas.map((area: SalesArea) => (
                <TableRow key={area.id}>
                  <TableCell className="font-medium">{area.area_code}</TableCell>
                  <TableCell>{area.area_name}</TableCell>
                  <TableCell>
                    <Badge variant={area.is_active ? 'default' : 'secondary'}>
                      {area.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(area)}>
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(area.id)}
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
              {editingArea ? 'Edit Sales Area' : 'Add Sales Area'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Area Code</label>
              <Input
                value={formData.area_code}
                onChange={(e) => setFormData({ ...formData, area_code: e.target.value })}
                placeholder="e.g., NORTH"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Area Name</label>
              <Input
                value={formData.area_name}
                onChange={(e) => setFormData({ ...formData, area_name: e.target.value })}
                placeholder="e.g., Northern Region"
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
              {editingArea ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

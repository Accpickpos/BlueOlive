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

interface SalesDepartment {
  id: number;
  department_number: number;
  department_name: string;
  is_active: boolean;
}

export default function DepartmentsPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingDept, setEditingDept] = useState<SalesDepartment | null>(null);
  const [formData, setFormData] = useState({
    department_number: 0,
    department_name: '',
    is_active: true,
  });

  const { data: departments, isLoading } = useQuery({
    queryKey: ['departments'],
    queryFn: () => apiRequest('/api/v1/settings/departments/'),
    select: (response) => response.data.results || response.data,
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      apiRequest('/api/v1/settings/departments/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] });
      setIsDialogOpen(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: typeof formData }) =>
      apiRequest(`/api/v1/settings/departments/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] });
      setIsDialogOpen(false);
      setEditingDept(null);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiRequest(`/api/v1/settings/departments/${id}/`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] });
    },
  });

  const resetForm = () => {
    setFormData({
      department_number: 0,
      department_name: '',
      is_active: true,
    });
  };

  const handleEdit = (dept: SalesDepartment) => {
    setEditingDept(dept);
    setFormData({
      department_number: dept.department_number,
      department_name: dept.department_name,
      is_active: dept.is_active,
    });
    setIsDialogOpen(true);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this department?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleSubmit = () => {
    if (editingDept) {
      updateMutation.mutate({ id: editingDept.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const filteredDepts = departments?.filter((dept: SalesDepartment) =>
    dept.department_number?.toString().includes(searchTerm) ||
    dept.department_name?.toLowerCase().includes(searchTerm.toLowerCase())
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
          <h1 className="text-3xl font-bold">Sales Departments</h1>
          <p className="text-gray-600 mt-1">Sales department setup</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by number or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            onClick={() => {
              resetForm();
              setEditingDept(null);
              setIsDialogOpen(true);
            }}
            className="ml-4"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Department
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading departments...</p>
          </div>
        ) : filteredDepts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No departments found. Click "Add Department" to create one.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Department Number</TableHead>
                <TableHead>Department Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDepts.map((dept: SalesDepartment) => (
                <TableRow key={dept.id}>
                  <TableCell className="font-medium">{dept.department_number}</TableCell>
                  <TableCell>{dept.department_name}</TableCell>
                  <TableCell>
                    <Badge variant={dept.is_active ? 'default' : 'secondary'}>
                      {dept.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(dept)}>
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(dept.id)}
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
              {editingDept ? 'Edit Department' : 'Add Department'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Department Number</label>
              <Input
                type="number"
                value={formData.department_number}
                onChange={(e) =>
                  setFormData({ ...formData, department_number: parseInt(e.target.value) || 0 })
                }
                placeholder="e.g., 1"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Department Name</label>
              <Input
                value={formData.department_name}
                onChange={(e) => setFormData({ ...formData, department_name: e.target.value })}
                placeholder="e.g., Electronics"
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
              {editingDept ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

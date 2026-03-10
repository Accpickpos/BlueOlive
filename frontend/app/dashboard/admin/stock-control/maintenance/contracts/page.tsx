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

interface ContractPricing {
  id: number;
  debtor: number;
  debtor_name?: string;
  stock_item: string;
  stock_item_description?: string;
  contract_price: number;
  valid_from: string;
  valid_until: string;
  is_active: boolean;
}

interface ContractFormData {
  debtor: string;
  stock_item: string;
  contract_price: number;
  valid_from: string;
  valid_until: string;
  is_active: boolean;
}

interface ContractSubmitData {
  debtor: number;
  stock_item: string;
  contract_price: number;
  valid_from: string;
  valid_until: string;
  is_active: boolean;
}

export default function ContractsPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingContract, setEditingContract] = useState<ContractPricing | null>(null);
  const [formData, setFormData] = useState<ContractFormData>({
    debtor: '',
    stock_item: '',
    contract_price: 0,
    valid_from: '',
    valid_until: '',
    is_active: true,
  });

  const { data: contracts, isLoading } = useQuery({
    queryKey: ['contract-pricing'],
    queryFn: () => apiRequest('/api/v1/stock-control/contract-pricing/'),
    select: (response) => response.data.results || response.data,
  });

  const { data: debtors } = useQuery({
    queryKey: ['debtors'],
    queryFn: () => apiRequest('/api/v1/debtors/'),
    select: (response) => response.data.results || response.data,
  });

  const { data: stockItems } = useQuery({
    queryKey: ['stock-items'],
    queryFn: () => apiRequest('/api/v1/stock-control/stock-items/'),
    select: (response) => response.data.results || response.data,
  });

  const createMutation = useMutation({
    mutationFn: (data: ContractSubmitData) =>
      apiRequest('/api/v1/stock-control/contract-pricing/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contract-pricing'] });
      setIsDialogOpen(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: ContractSubmitData }) =>
      apiRequest(`/api/v1/stock-control/contract-pricing/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contract-pricing'] });
      setIsDialogOpen(false);
      setEditingContract(null);
      resetForm();
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiRequest(`/api/v1/stock-control/contract-pricing/${id}/`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contract-pricing'] });
    },
  });

  const resetForm = () => {
    setFormData({
      debtor: '',
      stock_item: '',
      contract_price: 0,
      valid_from: '',
      valid_until: '',
      is_active: true,
    });
  };

  const handleEdit = (contract: ContractPricing) => {
    setEditingContract(contract);
    setFormData({
      debtor: contract.debtor.toString(),
      stock_item: contract.stock_item,
      contract_price: contract.contract_price,
      valid_from: contract.valid_from,
      valid_until: contract.valid_until,
      is_active: contract.is_active,
    });
    setIsDialogOpen(true);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this contract pricing?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleSubmit = () => {
    const payload: ContractSubmitData = {
      debtor: parseInt(formData.debtor),
      stock_item: formData.stock_item,
      contract_price: typeof formData.contract_price === 'string' ? parseFloat(formData.contract_price) : formData.contract_price,
      valid_from: formData.valid_from,
      valid_until: formData.valid_until,
      is_active: formData.is_active,
    };
    if (editingContract) {
      updateMutation.mutate({ id: editingContract.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const filteredContracts = contracts?.filter((contract: ContractPricing) =>
    contract.debtor_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contract.stock_item?.toLowerCase().includes(searchTerm.toLowerCase())
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
          <h1 className="text-3xl font-bold">Contract Pricing</h1>
          <p className="text-gray-600 mt-1">Debtor-specific pricing management</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by debtor or stock code..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            onClick={() => {
              resetForm();
              setEditingContract(null);
              setIsDialogOpen(true);
            }}
            className="ml-4"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Contract Pricing
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading contract pricing...</p>
          </div>
        ) : filteredContracts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No contract pricing found. Click "Add Contract Pricing" to create one.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Debtor</TableHead>
                <TableHead>Stock Code</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Contract Price</TableHead>
                <TableHead>Valid From</TableHead>
                <TableHead>Valid Until</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredContracts.map((contract: ContractPricing) => (
                <TableRow key={contract.id}>
                  <TableCell className="font-medium">{contract.debtor_name || contract.debtor}</TableCell>
                  <TableCell>{contract.stock_item}</TableCell>
                  <TableCell>{contract.stock_item_description || '-'}</TableCell>
                  <TableCell>${contract.contract_price.toFixed(2)}</TableCell>
                  <TableCell>{formatDate(contract.valid_from)}</TableCell>
                  <TableCell>{formatDate(contract.valid_until)}</TableCell>
                  <TableCell>
                    <Badge variant={contract.is_active ? 'default' : 'secondary'}>
                      {contract.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(contract)}>
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(contract.id)}
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
              {editingContract ? 'Edit Contract Pricing' : 'Add Contract Pricing'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Debtor</label>
              <Select
                value={formData.debtor}
                onValueChange={(value) => setFormData({ ...formData, debtor: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select debtor" />
                </SelectTrigger>
                <SelectContent>
                  {debtors?.map((debtor: any) => (
                    <SelectItem key={debtor.id} value={debtor.id.toString()}>
                      {debtor.dname || debtor.account_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
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
              <label className="text-sm font-medium">Contract Price</label>
              <Input
                type="number"
                step="0.01"
                value={formData.contract_price}
                onChange={(e) =>
                  setFormData({ ...formData, contract_price: parseFloat(e.target.value) || 0 })
                }
                placeholder="e.g., 99.99"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Valid From</label>
              <Input
                type="date"
                value={formData.valid_from}
                onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Valid Until</label>
              <Input
                type="date"
                value={formData.valid_until}
                onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })}
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
              {editingContract ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

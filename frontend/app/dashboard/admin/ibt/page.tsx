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
import { Plus, Search, Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

interface BranchTransfer {
  id: number;
  transfer_number: string;
  from_branch: string;
  to_branch: string;
  status: string;
  created_at: string;
  dispatched_at?: string;
  received_at?: string;
}

const statusColors: Record<string, string> = {
  PENDING: 'bg-yellow-500',
  APPROVED: 'bg-blue-500',
  DISPATCHED: 'bg-purple-500',
  IN_TRANSIT: 'bg-orange-500',
  RECEIVED: 'bg-green-500',
  CANCELLED: 'bg-red-500',
};

export default function IBTPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    from_branch: '',
    to_branch: '',
    notes: '',
  });

  const { data: transfers, isLoading, refetch } = useQuery({
    queryKey: ['branch-transfers', searchTerm],
    queryFn: () => apiRequest('/api/v1/stock-control/branch-transfers/'),
    select: (response) => response.data.results || response.data,
  });

  const { data: branches } = useQuery({
    queryKey: ['branches'],
    queryFn: () => apiRequest('/api/v1/stock-control/branches/'),
    select: (response) => response.data.results || response.data,
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      apiRequest('/api/v1/stock-control/branch-transfers/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-transfers'] });
      setIsDialogOpen(false);
      setFormData({ from_branch: '', to_branch: '', notes: '' });
    },
  });

  const filteredTransfers = transfers?.filter((transfer: BranchTransfer) =>
    transfer.transfer_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    transfer.from_branch?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    transfer.to_branch?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

  const handleCreateTransfer = () => {
    if (!formData.from_branch || !formData.to_branch) return;
    if (formData.from_branch === formData.to_branch) {
      alert('Source and destination branches must be different');
      return;
    }
    createMutation.mutate(formData);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Inter-Branch Transfers (IBT)</h1>
          <p className="text-gray-600 mt-1">Manage stock transfers between branches</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by transfer number, branch..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            onClick={() => setIsDialogOpen(true)}
            className="ml-4"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Transfer
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading transfers...</p>
          </div>
        ) : filteredTransfers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No transfers found. Click "New Transfer" to create one.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Transfer #</TableHead>
                <TableHead>From Branch</TableHead>
                <TableHead>To Branch</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Dispatched</TableHead>
                <TableHead>Received</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTransfers.map((transfer: BranchTransfer) => (
                <TableRow key={transfer.id}>
                  <TableCell className="font-medium">{transfer.transfer_number}</TableCell>
                  <TableCell>{transfer.from_branch}</TableCell>
                  <TableCell>{transfer.to_branch}</TableCell>
                  <TableCell>
                    <Badge className={statusColors[transfer.status] || 'bg-gray-500'}>
                      {transfer.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDate(transfer.created_at)}</TableCell>
                  <TableCell>{formatDate(transfer.dispatched_at)}</TableCell>
                  <TableCell>{formatDate(transfer.received_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create New Transfer</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Source Branch</label>
              <Select
                value={formData.from_branch}
                onValueChange={(value) => setFormData({ ...formData, from_branch: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select source branch" />
                </SelectTrigger>
                <SelectContent>
                  {branches?.map((branch: any) => (
                    <SelectItem key={branch.branch_code} value={branch.branch_code}>
                      {branch.branch_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Destination Branch</label>
              <Select
                value={formData.to_branch}
                onValueChange={(value) => setFormData({ ...formData, to_branch: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select destination branch" />
                </SelectTrigger>
                <SelectContent>
                  {branches?.map((branch: any) => (
                    <SelectItem key={branch.branch_code} value={branch.branch_code}>
                      {branch.branch_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Notes</label>
              <Input
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Optional notes"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateTransfer}
              disabled={createMutation.isPending || !formData.from_branch || !formData.to_branch}
            >
              {createMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : null}
              Create Transfer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

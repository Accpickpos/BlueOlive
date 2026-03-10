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

interface BranchTransferInvoice {
  id: number;
  invoice_number: string;
  transfer: number;
  transfer_number?: string;
  from_branch: string;
  to_branch: string;
  total_amount: number;
  status: string;
  issued_at?: string;
  paid_at?: string;
}

interface IBIFormData {
  transfer: string;
}

interface IBISubmitData {
  transfer: number;
}

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-500',
  ISSUED: 'bg-blue-500',
  PAID: 'bg-green-500',
  CANCELLED: 'bg-red-500',
};

export default function IBIPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState<IBIFormData>({
    transfer: '',
  });

  const { data: invoices, isLoading } = useQuery({
    queryKey: ['branch-transfer-invoices', searchTerm],
    queryFn: () => apiRequest('/api/v1/stock-control/branch-transfer-invoices/'),
    select: (response) => response.data.results || response.data,
  });

  const { data: transfers } = useQuery({
    queryKey: ['branch-transfers'],
    queryFn: () => apiRequest('/api/v1/stock-control/branch-transfers/'),
    select: (response) => response.data.results || response.data,
  });

  const createMutation = useMutation({
    mutationFn: (data: IBISubmitData) =>
      apiRequest('/api/v1/stock-control/branch-transfer-invoices/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-transfer-invoices'] });
      setIsDialogOpen(false);
      setFormData({ transfer: '' });
    },
  });

  const issueMutation = useMutation({
    mutationFn: (id: number) =>
      apiRequest(`/api/v1/stock-control/branch-transfer-invoices/${id}/issue/`, {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-transfer-invoices'] });
    },
  });

  const paidMutation = useMutation({
    mutationFn: (id: number) =>
      apiRequest(`/api/v1/stock-control/branch-transfer-invoices/${id}/mark-paid/`, {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-transfer-invoices'] });
    },
  });

  const filteredInvoices = invoices?.filter((invoice: BranchTransferInvoice) =>
    invoice.invoice_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.transfer_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.from_branch?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.to_branch?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

  const formatCurrency = (amount: number) => {
    return `$${amount?.toFixed(2) || '0.00'}`;
  };

  const handleCreateInvoice = () => {
    if (!formData.transfer) return;
    const payload: IBISubmitData = { transfer: parseInt(formData.transfer) };
    createMutation.mutate(payload);
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
          <h1 className="text-3xl font-bold">Inter-Branch Invoices (IBI)</h1>
          <p className="text-gray-600 mt-1">Manage inter-branch transfer invoices</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by item code, name, branch..."
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
            New Invoice
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading invoices...</p>
          </div>
        ) : filteredInvoices.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No invoices found. Click "New Invoice" to create one.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice #</TableHead>
                <TableHead>Transfer #</TableHead>
                <TableHead>From</TableHead>
                <TableHead>To</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Issued</TableHead>
                <TableHead>Paid</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredInvoices.map((invoice: BranchTransferInvoice) => (
                <TableRow key={invoice.id}>
                  <TableCell className="font-medium">{invoice.invoice_number}</TableCell>
                  <TableCell>{invoice.transfer_number}</TableCell>
                  <TableCell>{invoice.from_branch}</TableCell>
                  <TableCell>{invoice.to_branch}</TableCell>
                  <TableCell className="text-right font-medium">{formatCurrency(invoice.total_amount)}</TableCell>
                  <TableCell>
                    <Badge className={statusColors[invoice.status] || 'bg-gray-500'}>
                      {invoice.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDate(invoice.issued_at)}</TableCell>
                  <TableCell>{formatDate(invoice.paid_at)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {invoice.status === 'DRAFT' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => issueMutation.mutate(invoice.id)}
                        >
                          Issue
                        </Button>
                      )}
                      {invoice.status === 'ISSUED' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => paidMutation.mutate(invoice.id)}
                        >
                          Mark Paid
                        </Button>
                      )}
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
            <DialogTitle>Create New Invoice</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Transfer</label>
              <Select
                value={formData.transfer}
                onValueChange={(value) => setFormData({ transfer: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select transfer" />
                </SelectTrigger>
                <SelectContent>
                  {transfers
                    ?.filter((t: any) => t.status === 'RECEIVED')
                    .map((transfer: any) => (
                      <SelectItem key={transfer.id} value={transfer.id.toString()}>
                        {transfer.transfer_number} - {transfer.to_branch}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500 mt-1">
                Only received transfers can be invoiced
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateInvoice}
              disabled={createMutation.isPending || !formData.transfer}
            >
              {createMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : null}
              Create Invoice
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

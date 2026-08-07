'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { stockControlApi } from '@/lib/stockControlApi';
import { getStockItems } from '@/lib/stockApi';
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
import { Plus, Search, Loader2, ArrowLeft, Package } from 'lucide-react';
import Link from 'next/link';
import type { BranchTransfer } from '@/lib/types/stockControl';

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-400',
  PENDING: 'bg-yellow-500',
  APPROVED: 'bg-indigo-500',
  DISPATCHED: 'bg-blue-500',
  IN_TRANSIT: 'bg-blue-500',
  RECEIVED: 'bg-teal-500',
  COMPLETED: 'bg-green-500',
  CANCELLED: 'bg-red-500',
};

export default function StockConsolidationPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isItemsDialogOpen, setIsItemsDialogOpen] = useState(false);
  const [selectedTransfer, setSelectedTransfer] = useState<BranchTransfer | null>(null);
  const [formData, setFormData] = useState({
    from_branch: '',
    to_branch: '',
    notes: '',
  });
  const [newItem, setNewItem] = useState({ stock_code: '', quantity_requested: 0 });
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const { data: transfers, isLoading } = useQuery({
    queryKey: ['branch-transfers'],
    queryFn: () => stockControlApi.branchTransfers.list(),
  });

  const { data: branches } = useQuery({
    queryKey: ['branches'],
    queryFn: () => stockControlApi.branches.list(),
  });

  const { data: selectedTransferDetail } = useQuery({
    queryKey: ['branch-transfer', selectedTransfer?.id],
    queryFn: () => stockControlApi.branchTransfers.get(selectedTransfer!.id),
    enabled: !!selectedTransfer,
  });

  const { data: stockItems } = useQuery({
    queryKey: ['stock-items-search'],
    queryFn: () => getStockItems({ page_size: 100 }),
    staleTime: 5 * 60 * 1000,
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      stockControlApi.branchTransfers.create({
        transfer_number: `CONS-${Date.now()}`,
        from_branch: data.from_branch,
        to_branch: data.to_branch,
        notes: data.notes,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-transfers'] });
      setIsDialogOpen(false);
      setFormData({ from_branch: '', to_branch: '', notes: '' });
    },
  });

  const addItemMutation = useMutation({
    mutationFn: () =>
      stockControlApi.branchTransferItems.create({
        transfer: selectedTransfer!.id,
        stock_item: newItem.stock_code,
        quantity_requested: newItem.quantity_requested,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-transfer', selectedTransfer?.id] });
      setNewItem({ stock_code: '', quantity_requested: 0 });
      setSearchResults([]);
    },
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) => stockControlApi.branchTransfers.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-transfers'] });
      queryClient.invalidateQueries({ queryKey: ['branch-transfer', selectedTransfer?.id] });
    },
  });

  const dispatchMutation = useMutation({
    mutationFn: (id: number) => stockControlApi.branchTransfers.dispatch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-transfers'] });
      queryClient.invalidateQueries({ queryKey: ['branch-transfer', selectedTransfer?.id] });
    },
  });

  const receiveMutation = useMutation({
    mutationFn: (id: number) => stockControlApi.branchTransfers.receive(id, []),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-transfers'] });
      queryClient.invalidateQueries({ queryKey: ['branch-transfer', selectedTransfer?.id] });
      setIsItemsDialogOpen(false);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) => stockControlApi.branchTransfers.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branch-transfers'] });
      queryClient.invalidateQueries({ queryKey: ['branch-transfer', selectedTransfer?.id] });
    },
  });

  const filteredTransfers = (transfers?.results || []).filter((t: BranchTransfer) =>
    t.transfer_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.from_branch?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.to_branch?.toLowerCase().includes(searchTerm.toLowerCase())
  );

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

  const handleViewItems = (transfer: BranchTransfer) => {
    setSelectedTransfer(transfer);
    setIsItemsDialogOpen(true);
  };

  const handleSearchStock = (value: string) => {
    setNewItem((prev) => ({ ...prev, stock_code: value }));
    if (value.length >= 2 && stockItems) {
      const filtered = stockItems.results.filter((item: any) =>
        item.stock_code.toLowerCase().includes(value.toLowerCase()) ||
        item.description.toLowerCase().includes(value.toLowerCase())
      );
      setSearchResults(filtered.slice(0, 10));
    } else {
      setSearchResults([]);
    }
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
          <h1 className="text-3xl font-bold">Stock Consolidation</h1>
          <p className="text-gray-600 mt-1">Move stock between branches (inter-branch transfer)</p>
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
            <Package className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No transfers found. Click "New Transfer" to create one.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Transfer #</TableHead>
                <TableHead>From</TableHead>
                <TableHead>To</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Requested</TableHead>
                <TableHead>Received</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTransfers.map((t: BranchTransfer) => (
                <TableRow key={t.id}>
                  <TableCell className="font-medium">{t.transfer_number}</TableCell>
                  <TableCell>{t.from_branch_detail?.branch_name || t.from_branch}</TableCell>
                  <TableCell>{t.to_branch_detail?.branch_name || t.to_branch}</TableCell>
                  <TableCell>
                    <Badge className={statusColors[t.status] || 'bg-gray-500'}>
                      {t.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDate(t.requested_date)}</TableCell>
                  <TableCell>{formatDate(t.received_date)}</TableCell>
                  <TableCell className="text-right">
                    <Button size="sm" variant="outline" onClick={() => handleViewItems(t)}>
                      View / Manage
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      {/* Create Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>New Inter-Branch Transfer</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">From Branch</label>
              <Select
                value={formData.from_branch}
                onValueChange={(value) => setFormData({ ...formData, from_branch: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select source branch" />
                </SelectTrigger>
                <SelectContent>
                  {branches?.results?.map((b: any) => (
                    <SelectItem key={b.branch_code} value={b.branch_code}>
                      {b.branch_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">To Branch</label>
              <Select
                value={formData.to_branch}
                onValueChange={(value) => setFormData({ ...formData, to_branch: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select destination branch" />
                </SelectTrigger>
                <SelectContent>
                  {branches?.results?.map((b: any) => (
                    <SelectItem key={b.branch_code} value={b.branch_code}>
                      {b.branch_name}
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

      {/* View / Manage Items Dialog */}
      <Dialog open={isItemsDialogOpen} onOpenChange={setIsItemsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Transfer {selectedTransferDetail?.transfer_number} — {selectedTransferDetail?.status}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {selectedTransferDetail?.status === 'DRAFT' || selectedTransferDetail?.status === 'PENDING' ? (
              <div className="grid grid-cols-3 gap-2 items-end relative">
                <div className="col-span-2 relative">
                  <label className="text-sm font-medium">Add Stock Item</label>
                  <Input
                    placeholder="Search stock code..."
                    value={newItem.stock_code}
                    onChange={(e) => handleSearchStock(e.target.value)}
                  />
                  {searchResults.length > 0 && (
                    <div className="absolute z-10 w-full mt-1 border rounded-lg divide-y bg-white shadow-lg max-h-40 overflow-y-auto">
                      {searchResults.map((item: any) => (
                        <button
                          key={item.stock_code}
                          onClick={() => {
                            setNewItem((prev) => ({ ...prev, stock_code: item.stock_code }));
                            setSearchResults([]);
                          }}
                          className="w-full px-3 py-1.5 text-left hover:bg-gray-50 text-sm"
                        >
                          <span className="font-mono">{item.stock_code}</span>
                          <span className="text-gray-500 ml-2">{item.description}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <div>
                  <label className="text-sm font-medium">Qty</label>
                  <Input
                    type="number"
                    value={newItem.quantity_requested}
                    onChange={(e) => setNewItem((prev) => ({ ...prev, quantity_requested: parseFloat(e.target.value) || 0 }))}
                  />
                </div>
                <Button
                  className="col-span-3"
                  size="sm"
                  disabled={!newItem.stock_code || newItem.quantity_requested <= 0 || addItemMutation.isPending}
                  onClick={() => addItemMutation.mutate()}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Item
                </Button>
              </div>
            ) : null}

            {selectedTransferDetail?.items?.length === 0 || !selectedTransferDetail?.items ? (
              <p className="text-gray-500 text-center py-4">No items on this transfer yet</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Stock Code</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Requested</TableHead>
                    <TableHead className="text-right">Dispatched</TableHead>
                    <TableHead className="text-right">Received</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {selectedTransferDetail.items.map((item: any) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">{item.stock_item}</TableCell>
                      <TableCell>{item.stock_item_detail?.description}</TableCell>
                      <TableCell className="text-right">{item.quantity_requested}</TableCell>
                      <TableCell className="text-right">{item.quantity_dispatched}</TableCell>
                      <TableCell className="text-right">{item.quantity_received}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
          <DialogFooter className="flex-wrap gap-2">
            {selectedTransferDetail && !['COMPLETED', 'CANCELLED'].includes(selectedTransferDetail.status) && (
              <Button
                variant="outline"
                className="text-red-600"
                onClick={() => cancelMutation.mutate(selectedTransferDetail.id)}
                disabled={cancelMutation.isPending}
              >
                Cancel Transfer
              </Button>
            )}
            {selectedTransferDetail?.status === 'PENDING' && (
              <Button onClick={() => approveMutation.mutate(selectedTransferDetail.id)} disabled={approveMutation.isPending}>
                Approve
              </Button>
            )}
            {selectedTransferDetail?.status === 'APPROVED' && (
              <Button onClick={() => dispatchMutation.mutate(selectedTransferDetail.id)} disabled={dispatchMutation.isPending}>
                Dispatch
              </Button>
            )}
            {(selectedTransferDetail?.status === 'DISPATCHED' || selectedTransferDetail?.status === 'IN_TRANSIT') && (
              <Button onClick={() => receiveMutation.mutate(selectedTransferDetail.id)} disabled={receiveMutation.isPending}>
                Receive
              </Button>
            )}
            <Button variant="outline" onClick={() => setIsItemsDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

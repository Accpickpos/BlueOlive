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
import { Plus, Search, Loader2, ArrowLeft, Package } from 'lucide-react';
import Link from 'next/link';

interface StockItem {
  id: number;
  item_code: string;
  description: string;
  barcode?: string;
  category?: string;
  current_stock: number;
  unit_cost: number;
  unit_price: number;
}

interface Consolidation {
  id: number;
  consolidation_number: string;
  status: string;
  source_location: string;
  target_location: string;
  total_items: number;
  created_at: string;
  completed_at?: string;
}

const statusColors: Record<string, string> = {
  PENDING: 'bg-yellow-500',
  IN_PROGRESS: 'bg-blue-500',
  COMPLETED: 'bg-green-500',
  CANCELLED: 'bg-red-500',
};

export default function StockConsolidationPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isItemsDialogOpen, setIsItemsDialogOpen] = useState(false);
  const [selectedConsolidation, setSelectedConsolidation] = useState<Consolidation | null>(null);
  const [formData, setFormData] = useState({
    source_location: '',
    target_location: '',
    notes: '',
  });

  const { data: consolidations, isLoading } = useQuery({
    queryKey: ['stock-consolidations', searchTerm],
    queryFn: () => apiRequest('/api/v1/stock-control/consolidations/'),
    select: (response) => response.data.results || response.data,
  });

  const { data: locations } = useQuery({
    queryKey: ['locations'],
    queryFn: () => apiRequest('/api/v1/stock-control/locations/'),
    select: (response) => response.data.results || response.data,
  });

  const { data: consolidationItems } = useQuery({
    queryKey: ['consolidation-items', selectedConsolidation?.id],
    queryFn: () => apiRequest(`/api/v1/stock-control/consolidations/${selectedConsolidation?.id}/items/`),
    enabled: !!selectedConsolidation,
    select: (response) => response.data.results || response.data,
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      apiRequest('/api/v1/stock-control/consolidations/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-consolidations'] });
      setIsDialogOpen(false);
      setFormData({ source_location: '', target_location: '', notes: '' });
    },
  });

  const completeMutation = useMutation({
    mutationFn: (id: number) =>
      apiRequest(`/api/v1/stock-control/consolidations/${id}/complete/`, {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-consolidations'] });
      setIsItemsDialogOpen(false);
    },
  });

  const filteredConsolidations = consolidations?.filter((cons: Consolidation) =>
    cons.consolidation_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cons.source_location?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cons.target_location?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

  const handleCreateConsolidation = () => {
    if (!formData.source_location || !formData.target_location) return;
    if (formData.source_location === formData.target_location) {
      alert('Source and destination locations must be different');
      return;
    }
    createMutation.mutate(formData);
  };

  const handleViewItems = (consolidation: Consolidation) => {
    setSelectedConsolidation(consolidation);
    setIsItemsDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Stock Consolidation</h1>
          <p className="text-gray-600 mt-1">Consolidate stock from multiple locations</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by consolidation number, location..."
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
            New Consolidation
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading consolidations...</p>
          </div>
        ) : filteredConsolidations.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Package className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No consolidations found. Click "New Consolidation" to create one.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Consolidation #</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Target</TableHead>
                <TableHead className="text-center">Items</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Completed</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredConsolidations.map((cons: Consolidation) => (
                <TableRow key={cons.id}>
                  <TableCell className="font-medium">{cons.consolidation_number}</TableCell>
                  <TableCell>{cons.source_location}</TableCell>
                  <TableCell>{cons.target_location}</TableCell>
                  <TableCell className="text-center">{cons.total_items}</TableCell>
                  <TableCell>
                    <Badge className={statusColors[cons.status] || 'bg-gray-500'}>
                      {cons.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDate(cons.created_at)}</TableCell>
                  <TableCell>{formatDate(cons.completed_at)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleViewItems(cons)}
                      >
                        View Items
                      </Button>
                      {cons.status === 'IN_PROGRESS' && (
                        <Button
                          size="sm"
                          onClick={() => completeMutation.mutate(cons.id)}
                        >
                          Complete
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

      {/* Create Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>New Stock Consolidation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Source Location</label>
              <Select
                value={formData.source_location}
                onValueChange={(value) => setFormData({ ...formData, source_location: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select source location" />
                </SelectTrigger>
                <SelectContent>
                  {locations?.map((loc: any) => (
                    <SelectItem key={loc.location_code} value={loc.location_code}>
                      {loc.location_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Target Location</label>
              <Select
                value={formData.target_location}
                onValueChange={(value) => setFormData({ ...formData, target_location: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select target location" />
                </SelectTrigger>
                <SelectContent>
                  {locations?.map((loc: any) => (
                    <SelectItem key={loc.location_code} value={loc.location_code}>
                      {loc.location_name}
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
              onClick={handleCreateConsolidation}
              disabled={createMutation.isPending || !formData.source_location || !formData.target_location}
            >
              {createMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : null}
              Create Consolidation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Items Dialog */}
      <Dialog open={isItemsDialogOpen} onOpenChange={setIsItemsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Consolidation Items - {selectedConsolidation?.consolidation_number}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {consolidationItems?.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No items in this consolidation</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Item Code</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {consolidationItems?.map((item: any) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">{item.item_code}</TableCell>
                      <TableCell>{item.description}</TableCell>
                      <TableCell className="text-right">{item.quantity}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsItemsDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

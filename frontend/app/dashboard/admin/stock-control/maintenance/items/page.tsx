'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getStockItems, deleteStockItem } from '@/lib/stockApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  Loader, Plus, Edit, Trash2, Search, 
  Package, AlertTriangle 
} from 'lucide-react';
import Link from 'next/link';

export default function StockItemsMaintenancePage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data: stockItems, isLoading } = useQuery({
    queryKey: ['stock-items', searchTerm, page],
    queryFn: () => getStockItems({ search: searchTerm, page }),
  });

  const deleteMutation = useMutation({
    mutationFn: (code: string) => deleteStockItem(code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-items'] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Stock Items Maintenance</h1>
          <p className="text-gray-600 mt-1">Create and manage stock items</p>
        </div>
        <Link href="/dashboard/admin/stock-control/maintenance/items/new">
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="w-4 h-4 mr-2" />
            New Stock Item
          </Button>
        </Link>
      </div>

      <Card className="p-4">
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by code or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select className="w-48">
            <option value="">All Departments</option>
          </Select>
        </div>
      </Card>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Code</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Department</TableHead>
              <TableHead>Supplier</TableHead>
              <TableHead className="text-right">QOH</TableHead>
              <TableHead className="text-right">Cost</TableHead>
              <TableHead className="text-right">Selling</TableHead>
              <TableHead className="text-center">Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {stockItems?.results?.map((item: any) => (
              <TableRow key={item.stock_code}>
                <TableCell className="font-mono">{item.stock_code}</TableCell>
                <TableCell>{item.description}</TableCell>
                <TableCell>{item.department_name || item.department}</TableCell>
                <TableCell>{item.supplier_name || item.supplier}</TableCell>
                <TableCell className="text-right">
                  <span className={item.quantity_on_hand <= 0 ? 'text-red-600 font-bold' : ''}>
                    {item.quantity_on_hand?.toFixed(2)}
                  </span>
                </TableCell>
                <TableCell className="text-right">R {item.cost_price?.toFixed(2)}</TableCell>
                <TableCell className="text-right">R {item.selling_price_1?.toFixed(2)}</TableCell>
                <TableCell className="text-center">
                  {item.quantity_on_hand <= item.reorder_quantity ? (
                    <div title="Low Stock"><AlertTriangle className="w-4 h-4 text-amber-500" /></div>
                  ) : item.quantity_on_hand <= 0 ? (
                    <div title="Out of Stock"><AlertTriangle className="w-4 h-4 text-red-500" /></div>
                  ) : (
                    <div title="In Stock"><Package className="w-4 h-4 text-green-500" /></div>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Link href={`/dashboard/admin/stock-control/maintenance/items/${item.stock_code}`}>
                      <Button variant="outline" size="sm"><Edit className="w-3 h-3" /></Button>
                    </Link>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        if (confirm('Delete this item?')) {
                          deleteMutation.mutate(item.stock_code);
                        }
                      }}
                    >
                      <Trash2 className="w-3 h-3 text-red-500" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {stockItems?.results && (
          <div className="flex items-center justify-between p-4 border-t">
            <p className="text-sm text-gray-600">
              Showing {((page - 1) * 20) + 1} to {Math.min(page * 20, stockItems.count)} of {stockItems.count}
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage(page - 1)}>
                Previous
              </Button>
              <Button variant="outline" size="sm" disabled={page >= Math.ceil(stockItems.count / 20)} onClick={() => setPage(page + 1)}>
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

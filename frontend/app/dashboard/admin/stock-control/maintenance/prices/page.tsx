'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiRequest } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Search, Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

interface StockItem {
  id: number;
  stock_code: string;
  description: string;
  cost_price: number;
  selling_price_1: number;
  selling_price_2: number;
  selling_price_3: number;
  markup_1: number;
  markup_2: number;
  markup_3: number;
  is_active: boolean;
}

export default function PricesPage() {
  const [searchTerm, setSearchTerm] = useState('');

  const { data: stockItems, isLoading } = useQuery({
    queryKey: ['stock-items'],
    queryFn: () => apiRequest('/api/v1/stock-control/stock-items/'),
    select: (response) => response.data.results || response.data,
  });

  const filteredItems = stockItems?.filter((item: StockItem) =>
    item.stock_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.description?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const formatCurrency = (value: number) => {
    if (!value && value !== 0) return '-';
    return `$${value.toFixed(2)}`;
  };

  const formatPercent = (value: number) => {
    if (!value && value !== 0) return '-';
    return `${value.toFixed(2)}%`;
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
          <h1 className="text-3xl font-bold">Prices</h1>
          <p className="text-gray-600 mt-1">Cost and selling price management</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by code or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading stock items...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No stock items found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Stock Code</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Cost Price</TableHead>
                  <TableHead className="text-right">Price 1</TableHead>
                  <TableHead className="text-right">Markup 1</TableHead>
                  <TableHead className="text-right">Price 2</TableHead>
                  <TableHead className="text-right">Markup 2</TableHead>
                  <TableHead className="text-right">Price 3</TableHead>
                  <TableHead className="text-right">Markup 3</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map((item: StockItem) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{item.stock_code}</TableCell>
                    <TableCell>{item.description}</TableCell>
                    <TableCell className="text-right">{formatCurrency(item.cost_price)}</TableCell>
                    <TableCell className="text-right font-medium">{formatCurrency(item.selling_price_1)}</TableCell>
                    <TableCell className="text-right">{formatPercent(item.markup_1)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(item.selling_price_2)}</TableCell>
                    <TableCell className="text-right">{formatPercent(item.markup_2)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(item.selling_price_3)}</TableCell>
                    <TableCell className="text-right">{formatPercent(item.markup_3)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>
    </div>
  );
}

import { Button } from '@/components/ui/button';

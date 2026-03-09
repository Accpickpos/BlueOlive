'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getStockItems, getStockSummary } from '@/lib/stockApi';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { 
  Loader, ArrowLeft, DollarSign, Package, TrendingUp, 
  Layers, PieChart, Download
} from 'lucide-react';
import Link from 'next/link';

export default function ValuationPage() {
  const [groupBy, setGroupBy] = useState('department');
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['stock-summary'],
    queryFn: getStockSummary,
    staleTime: 5 * 60 * 1000,
  });

  const { data: stockItems, isLoading: itemsLoading } = useQuery({
    queryKey: ['stock-items-valuation', page],
    queryFn: () => getStockItems({ 
      page, 
      page_size: pageSize,
      is_active: true,
      ordering: '-quantity_on_hand'
    }),
    staleTime: 30 * 1000,
  });

  // Calculate valuation by grouping
  const calculateValuationByDepartment = () => {
    if (!stockItems?.results) return [];
    
    const deptMap = new Map();
    stockItems.results.forEach((item: any) => {
      const deptName = item.department_detail?.name || 'Unassigned';
      const value = (item.quantity_on_hand || 0) * (item.cost_price || 0);
      const retailValue = (item.quantity_on_hand || 0) * (item.selling_price_1 || 0);
      
      if (deptMap.has(deptName)) {
        const existing = deptMap.get(deptName);
        existing.count += 1;
        existing.totalQuantity += item.quantity_on_hand || 0;
        existing.totalCostValue += value;
        existing.totalRetailValue += retailValue;
      } else {
        deptMap.set(deptName, {
          name: deptName,
          count: 1,
          totalQuantity: item.quantity_on_hand || 0,
          totalCostValue: value,
          totalRetailValue: retailValue,
        });
      }
    });
    
    return Array.from(deptMap.values()).sort((a, b) => b.totalCostValue - a.totalCostValue);
  };

  const { data: allStockItems } = useQuery({
    queryKey: ['stock-items-all'],
    queryFn: () => getStockItems({ page_size: 1000, is_active: true }),
    staleTime: 5 * 60 * 1000,
  });

  const calculateValuationByDepartmentAll = () => {
    if (!allStockItems?.results) return [];
    
    const deptMap = new Map();
    allStockItems.results.forEach((item: any) => {
      const deptName = item.department_detail?.name || 'Unassigned';
      const value = (item.quantity_on_hand || 0) * (item.cost_price || 0);
      const retailValue = (item.quantity_on_hand || 0) * (item.selling_price_1 || 0);
      
      if (deptMap.has(deptName)) {
        const existing = deptMap.get(deptName);
        existing.count += 1;
        existing.totalQuantity += item.quantity_on_hand || 0;
        existing.totalCostValue += value;
        existing.totalRetailValue += retailValue;
      } else {
        deptMap.set(deptName, {
          name: deptName,
          count: 1,
          totalQuantity: item.quantity_on_hand || 0,
          totalCostValue: value,
          totalRetailValue: retailValue,
        });
      }
    });
    
    return Array.from(deptMap.values()).sort((a, b) => b.totalCostValue - a.totalCostValue);
  };

  const valuationByDept = calculateValuationByDepartmentAll();
  const totalCostValue = valuationByDept.reduce((sum, d) => sum + d.totalCostValue, 0);
  const totalRetailValue = valuationByDept.reduce((sum, d) => sum + d.totalRetailValue, 0);
  const totalItems = valuationByDept.reduce((sum, d) => sum + d.count, 0);

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/stock-control/enquiries">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Stock Valuation</h1>
          <p className="text-gray-600 mt-1">View current stock value by category or department</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6 border-l-4 border-l-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Cost Value</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                R {totalCostValue.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-green-200" />
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Retail Value</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                R {totalRetailValue.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-blue-200" />
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Potential Profit</p>
              <p className="text-2xl font-bold text-purple-600 mt-1">
                R {(totalRetailValue - totalCostValue).toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <Package className="w-8 h-8 text-purple-200" />
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase">Total Items</p>
              <p className="text-2xl font-bold text-amber-600 mt-1">
                {totalItems.toLocaleString()}
              </p>
            </div>
            <Layers className="w-8 h-8 text-amber-200" />
          </div>
        </Card>
      </div>

      {/* Valuation by Department */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold flex items-center">
            <PieChart className="w-5 h-5 mr-2" />
            Valuation by Department
          </h2>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>

        {valuationByDept.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Department</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Item Count</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Total Qty</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Cost Value</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Retail Value</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">% of Total</th>
                  </tr>
                </thead>
                <tbody>
                  {valuationByDept.map((dept: any, idx: number) => (
                    <tr key={idx} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium">{dept.name}</td>
                      <td className="py-3 px-4 text-right">{dept.count}</td>
                      <td className="py-3 px-4 text-right">{dept.totalQuantity.toLocaleString('en-ZA', { maximumFractionDigits: 0 })}</td>
                      <td className="py-3 px-4 text-right font-medium">
                        R {dept.totalCostValue.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right">
                        R {dept.totalRetailValue.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-blue-600" 
                              style={{ width: `${(dept.totalCostValue / totalCostValue) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm">
                            {((dept.totalCostValue / totalCostValue) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-gray-100 font-bold">
                    <td className="py-3 px-4">TOTAL</td>
                    <td className="py-3 px-4 text-right">{totalItems}</td>
                    <td className="py-3 px-4 text-right">
                      {valuationByDept.reduce((sum, d) => sum + d.totalQuantity, 0).toLocaleString('en-ZA', { maximumFractionDigits: 0 })}
                    </td>
                    <td className="py-3 px-4 text-right">
                      R {totalCostValue.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right">
                      R {totalRetailValue.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right">100%</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </>
        ) : (
          <div className="text-center py-12">
            <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No stock data available</p>
          </div>
        )}
      </Card>

      {/* Top Stock Items by Value */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Top Stock Items by Value</h2>
        
        {itemsLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Stock Code</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Description</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Qty on Hand</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Unit Cost</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Total Value</th>
                </tr>
              </thead>
              <tbody>
                {stockItems?.results?.slice(0, 20).map((item: any) => {
                  const totalValue = (item.quantity_on_hand || 0) * (item.cost_price || 0);
                  return (
                    <tr key={item.stock_code} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 font-mono">{item.stock_code}</td>
                      <td className="py-3 px-4 max-w-xs truncate">{item.description}</td>
                      <td className="py-3 px-4 text-right">{item.quantity_on_hand?.toFixed(2) || '0.00'}</td>
                      <td className="py-3 px-4 text-right">R {item.cost_price?.toFixed(2) || '0.00'}</td>
                      <td className="py-3 px-4 text-right font-medium">
                        R {totalValue.toLocaleString('en-ZA', { maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

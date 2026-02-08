'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

interface DepartmentData {
  id: number;
  number: number;
  name: string;
  is_active: boolean;
  sales_mtd: number;
  sales_ytd: number;
  profit_mtd: number;
  profit_ytd: number;
  gross_profit_percent_mtd: number;
  gross_profit_percent_ytd: number;
}

interface DepartmentListData {
  results: DepartmentData[];
}

// Helper function to safely format currency
const formatCurrency = (value: any): string => {
  const num = typeof value === 'string' ? parseFloat(value) : Number(value);
  return isNaN(num) ? '0.00' : num.toFixed(2);
};

// Helper function to safely format percentage
const formatPercent = (value: any): string => {
  const num = typeof value === 'string' ? parseFloat(value) : Number(value);
  return isNaN(num) ? '0.00' : num.toFixed(2);
};

export default function SalesDepartmentsEnquiry() {
  const [departmentId, setDepartmentId] = useState('');
  const [viewType, setViewType] = useState<'table' | 'chart'>('table');
  const [departmentData, setDepartmentData] = useState<DepartmentData | null>(null);
  const [departmentsList, setDepartmentsList] = useState<DepartmentData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const searchDepartment = async () => {
    if (!departmentId) {
      setError('Please enter a department ID');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const response = await apiRequest(`/api/v1/settings/departments/${departmentId}/`);
      const responseData = (response as any).data || (response as any);
      
      // Convert string numbers to actual numbers
      const dept: DepartmentData = {
        ...responseData,
        sales_mtd: Number(responseData.sales_mtd) || 0,
        sales_ytd: Number(responseData.sales_ytd) || 0,
        profit_mtd: Number(responseData.profit_mtd) || 0,
        profit_ytd: Number(responseData.profit_ytd) || 0,
        gross_profit_percent_mtd: Number(responseData.gross_profit_percent_mtd) || 0,
        gross_profit_percent_ytd: Number(responseData.gross_profit_percent_ytd) || 0,
      };
      
      setDepartmentData(dept);
      setDepartmentsList([]);
    } catch (err) {
      setError('Department not found');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const viewAll = async () => {
    setLoading(true);
    setError('');
    setDepartmentData(null);
    try {
      const response = await apiRequest('/api/v1/settings/departments/?is_active=true');
      const responseData = (response as any).data || (response as any);
      const departments: any[] = responseData.results || (Array.isArray(responseData) ? responseData : []);
      
      // Convert string numbers to actual numbers
      const convertedDepartments: DepartmentData[] = departments.map(d => ({
        ...d,
        sales_mtd: Number(d.sales_mtd) || 0,
        sales_ytd: Number(d.sales_ytd) || 0,
        profit_mtd: Number(d.profit_mtd) || 0,
        profit_ytd: Number(d.profit_ytd) || 0,
        gross_profit_percent_mtd: Number(d.gross_profit_percent_mtd) || 0,
        gross_profit_percent_ytd: Number(d.gross_profit_percent_ytd) || 0,
      }));
      
      // Filter to show only departments with sales activity (sales_ytd > 0)
      const departmentsWithSales = convertedDepartments.filter(d => d.sales_ytd > 0);
      
      if (departmentsWithSales.length > 0) {
        setDepartmentsList(departmentsWithSales);
      } else {
        setError('No departments with sales activity found');
        setDepartmentsList(convertedDepartments); // Show all active departments even if no sales
      }
    } catch (err) {
      setError('Failed to load departments');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-900">Sales Departments Performance</h2>

      {/* Filters */}
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
        <h3 className="font-semibold text-gray-900">Department Selection</h3>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Department #</label>
            <input
              type="text"
              value={departmentId}
              onChange={(e) => setDepartmentId(e.target.value)}
              placeholder="Enter or search department"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-600 mt-1">Press Page Down for ALL Departments</p>
          </div>

          <div className="flex items-end gap-2">
            <button 
              onClick={searchDepartment}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Search Department'}
            </button>
            <button 
              onClick={viewAll}
              disabled={loading}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium disabled:opacity-50"
            >
              View All
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* View Type Selector */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setViewType('table')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            viewType === 'table'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Table View
        </button>
        <button
          onClick={() => setViewType('chart')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            viewType === 'chart'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Chart View
        </button>
      </div>

      {/* Summary Stats */}
      {departmentData && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
            <p className="text-xs text-blue-700 font-medium">Sales YTD</p>
            <p className="text-2xl font-bold text-blue-900">R{formatCurrency(departmentData.sales_ytd)}</p>
            <p className="text-xs text-blue-600 mt-1">Year to Date</p>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
            <p className="text-xs text-green-700 font-medium">Profit YTD</p>
            <p className="text-2xl font-bold text-green-900">R{formatCurrency(departmentData.profit_ytd)}</p>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
            <p className="text-xs text-purple-700 font-medium">Profit %</p>
            <p className="text-2xl font-bold text-purple-900">{formatPercent(departmentData.gross_profit_percent_ytd)}%</p>
          </div>
        </div>
      )}

      {/* Table View */}
      {viewType === 'table' && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100 border-b border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Department</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Sales MTD</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Sales YTD</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Profit MTD</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Profit YTD</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Profit % YTD</th>
                </tr>
              </thead>
              <tbody>
                {departmentsList.length > 0 ? (
                  departmentsList.map((dept) => (
                    <tr key={dept.id} className="border-b border-gray-200 hover:bg-gray-50 cursor-pointer" onClick={() => setDepartmentData(dept)}>
                      <td className="px-4 py-3 font-medium text-gray-900">{dept.number} - {dept.name}</td>
                      <td className="px-4 py-3 text-right text-gray-700">R{formatCurrency(dept.sales_mtd)}</td>
                      <td className="px-4 py-3 text-right font-medium text-gray-900">R{formatCurrency(dept.sales_ytd)}</td>
                      <td className="px-4 py-3 text-right text-gray-700">R{formatCurrency(dept.profit_mtd)}</td>
                      <td className="px-4 py-3 text-right text-gray-700">R{formatCurrency(dept.profit_ytd)}</td>
                      <td className="px-4 py-3 text-right font-medium">{formatPercent(dept.gross_profit_percent_ytd)}%</td>
                    </tr>
                  ))
                ) : departmentData ? (
                  <tr className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{departmentData.number} - {departmentData.name}</td>
                    <td className="px-4 py-3 text-right text-gray-700">R{formatCurrency(departmentData.sales_mtd)}</td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">R{formatCurrency(departmentData.sales_ytd)}</td>
                    <td className="px-4 py-3 text-right text-gray-700">R{formatCurrency(departmentData.profit_mtd)}</td>
                    <td className="px-4 py-3 text-right text-gray-700">R{formatCurrency(departmentData.profit_ytd)}</td>
                    <td className="px-4 py-3 text-right font-medium">{formatPercent(departmentData.gross_profit_percent_ytd)}%</td>
                  </tr>
                ) : (
                  <tr className="border-b border-gray-200 hover:bg-gray-50">
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                      Click "View All" to see all departments with sales activity
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Chart View */}
      {viewType === 'chart' && (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center text-gray-500">
          <p className="text-lg">Graphical representation of monthly sales performance</p>
          <p className="text-sm mt-2">Select a department to view chart</p>
        </div>
      )}
    </div>
  );
}

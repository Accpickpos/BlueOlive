'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

interface SalesmanData {
  id: number;
  number: number;
  name: string;
  user_username?: string;
  commission_rate: number;
  is_active: boolean;
  sales_mtd: number;
  sales_ytd: number;
  profit_mtd: number;
  profit_ytd: number;
  commission_mtd: number;
  commission_ytd: number;
  gross_profit_percent_mtd: number;
  gross_profit_percent_ytd: number;
  sales_by_month?: Record<string, number>;
}

export default function SalesmanEnquiry() {
  const [salesman, setSalesman] = useState('');
  const [viewType, setViewType] = useState<'table' | 'chart'>('table');
  const [salesmanData, setSalesmanData] = useState<SalesmanData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const searchSalesman = async () => {
    if (!salesman) {
      setError('Please enter a salesman name');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.append('name', salesman);
      const response = await apiRequest(`/api/settings/sales-areas/?${params}`);
      const responseData = (response as any).data || (response as any);
      const data = responseData.results ? responseData.results[0] : responseData;
      setSalesmanData(data);
    } catch (err) {
      setError('Salesman not found');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const viewAll = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiRequest('/api/settings/sales-areas/');
      const responseData = (response as any).data || (response as any);
      const salesmen = responseData.results || responseData;
      if (Array.isArray(salesmen) && salesmen.length > 0) {
        setSalesmanData(salesmen[0]);
      }
    } catch (err) {
      setError('Failed to load salesmen');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-900">Salesman Performance</h2>

      {/* Filters */}
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
        <h3 className="font-semibold text-gray-900">Salesman Selection</h3>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Salesman Name</label>
            <input
              type="text"
              value={salesman}
              onChange={(e) => setSalesman(e.target.value)}
              placeholder="Enter or search salesman"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-end gap-2">
            <button 
              onClick={searchSalesman}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 text-sm font-medium"
            >
              {loading ? 'Loading...' : 'Search Salesman'}
            </button>
            <button 
              onClick={viewAll}
              disabled={loading}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-400 text-sm font-medium"
            >
              View All
            </button>
          </div>
        </div>
      </div>

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

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <p className="text-xs text-blue-700 font-medium">Sales YTD</p>
          <p className="text-2xl font-bold text-blue-900">R{(salesmanData?.sales_ytd || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
          <p className="text-xs text-blue-600 mt-1">Year to Date</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
          <p className="text-xs text-green-700 font-medium">Profit YTD</p>
          <p className="text-2xl font-bold text-green-900">R{(salesmanData?.profit_ytd || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
          <p className="text-xs text-purple-700 font-medium">Commission YTD</p>
          <p className="text-2xl font-bold text-purple-900">R{(salesmanData?.commission_ytd || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
        </div>
      </div>

      {/* Table View */}
      {viewType === 'table' && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100 border-b border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Salesman</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Sales MTD</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Sales YTD</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Profit MTD</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Profit YTD</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Commission YTD</th>
                </tr>
              </thead>
              <tbody>
                {salesmanData ? (
                  <tr className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{salesmanData.number} - {salesmanData.name}</td>
                    <td className="px-4 py-3 text-right">R{(salesmanData.sales_mtd || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 text-right">R{(salesmanData.sales_ytd || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 text-right">R{(salesmanData.profit_mtd || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 text-right">R{(salesmanData.profit_ytd || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 text-right font-medium">R{(salesmanData.commission_ytd || 0).toLocaleString('en-ZA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  </tr>
                ) : (
                  <tr className="border-b border-gray-200 hover:bg-gray-50">
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                      Select a salesman to view performance
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
          <p className="text-sm mt-2">Select a salesman to view chart</p>
        </div>
      )}
    </div>
  );
}

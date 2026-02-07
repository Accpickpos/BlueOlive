'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Printer, Download } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface PrintStockTakeFormsProps {
  onBack: () => void;
}

export default function PrintStockTakeForms({ onBack }: PrintStockTakeFormsProps) {
  const [sortOrder, setSortOrder] = useState('code');
  const [filterDepartment, setFilterDepartment] = useState('');
  const [filterStatus, setFilterStatus] = useState('active');
  const [isPrinting, setIsPrinting] = useState(false);

  // Fetch departments
  const { data: departments } = useQuery({
    queryKey: ['departments'],
    queryFn: async () => {
      const response = await api.get('/api/settings/departments/');
      return response.data.results || response.data;
    },
  });

  const handlePrint = async () => {
    try {
      setIsPrinting(true);
      
      // Build query parameters
      const params = new URLSearchParams({
        sort_order: sortOrder,
        ...(filterDepartment && { department: filterDepartment }),
        filter_status: filterStatus,
      });

      // Fetch stock items to print
      const response = await api.get(`/api/stock-control/stock-items/?${params}`);
      const items = response.data.results || response.data;

      // Generate print content
      const printWindow = window.open('', '', 'width=800,height=600');
      if (printWindow) {
        let html = `
          <html>
            <head>
              <title>Stock Take Forms</title>
              <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { text-align: center; margin-bottom: 20px; }
                .form-section { page-break-after: always; border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; }
                table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f0f0f0; font-weight: bold; }
                .lines { height: 25px; }
              </style>
            </head>
            <body>
              <h1>Stock Take Form</h1>
              <p>Date: <u style="width: 150px; display: inline-block;"></u></p>
              <p>Department: <u style="width: 150px; display: inline-block;"></u></p>
              
              <table>
                <thead>
                  <tr>
                    <th>Stock Code</th>
                    <th>Description</th>
                    <th>System Qty</th>
                    <th>Counted Qty</th>
                    <th>Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  ${items
                    .map(
                      (item: any) => `
                    <tr>
                      <td>${item.stock_code}</td>
                      <td>${item.description}</td>
                      <td>${item.quantity_on_hand}</td>
                      <td style="text-align: center;" class="lines"></td>
                      <td style="text-align: center;" class="lines"></td>
                    </tr>
                  `
                    )
                    .join('')}
                </tbody>
              </table>
            </body>
          </html>
        `;
        printWindow.document.write(html);
        printWindow.document.close();
        printWindow.print();
      }
    } finally {
      setIsPrinting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          <ArrowLeft size={20} />
          Back
        </button>
        <h3 className="text-2xl font-bold">Print Stock Take Forms</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div>
          <label className="block text-sm font-medium mb-2">Sort Order</label>
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="code">Stock Code</option>
            <option value="description">Description</option>
            <option value="department">Department</option>
            <option value="supplier">Supplier Code</option>
            <option value="bin">Bin Number</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Filter by Department</label>
          <select
            value={filterDepartment}
            onChange={(e) => setFilterDepartment(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Departments</option>
            {departments?.map((dept: any) => (
              <option key={dept.id} value={dept.id}>
                {dept.department_name || dept.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Filter by Status</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="active">Active Items Only</option>
            <option value="all">All Items</option>
            <option value="inactive">Inactive Items</option>
          </select>
        </div>
      </div>

      <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
        <p className="text-sm text-gray-700">
          <strong>Note:</strong> Forms will be sorted by {sortOrder}. Each page contains a blank table for manual entry of counted quantities.
        </p>
      </div>

      <div className="flex gap-4 justify-center">
        <button
          onClick={onBack}
          className="px-6 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition"
        >
          Cancel
        </button>
        <button
          onClick={handlePrint}
          disabled={isPrinting}
          className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
        >
          <Printer size={20} />
          {isPrinting ? 'Preparing...' : 'Print Forms'}
        </button>
      </div>
    </div>
  );
}

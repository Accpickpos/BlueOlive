'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

interface MonthlySales {
  month: string;
  sales_amount: number;
  transactions_count: number;
}

interface SalesAnalysisProps {
  debtorId: number;
}

export default function SalesAnalysis({ debtorId }: SalesAnalysisProps) {
  const [monthlySales, setMonthlySales] = useState<MonthlySales[]>([]);
  const [ytdTotal, setYtdTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadSalesAnalysis();
  }, [debtorId]);

  const loadSalesAnalysis = async () => {
    try {
      // Get transactions for this debtor - filter by debtor_id in query params
      const response = await apiRequest(`/api/v1/debtors/transactions/?debtor=${debtorId}`);
      
      if ((response as any).results) {
        processSalesData((response as any).results);
      } else if (Array.isArray(response)) {
        processSalesData(response);
      }
    } catch (err) {
      setError('Failed to load sales analysis');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const processSalesData = (transactions: any[]) => {
    const salesByMonth: Record<string, { amount: number; count: number }> = {};
    const currentYear = new Date().getFullYear();
    let ytd = 0;

    // Group by month
    transactions.forEach(tx => {
      const date = new Date(tx.transaction_date);
      
      // Only include current year for YTD
      if (date.getFullYear() === currentYear) {
        const monthKey = date.toLocaleString('default', { month: 'long', year: 'numeric' });
        
        if (!salesByMonth[monthKey]) {
          salesByMonth[monthKey] = { amount: 0, count: 0 };
        }

        // Include invoices and receipts as sales
        if (['INV', 'CSH', 'RCT'].includes(tx.transaction_type)) {
          salesByMonth[monthKey].amount += parseFloat(tx.total_amount);
          salesByMonth[monthKey].count += 1;
          ytd += parseFloat(tx.total_amount);
        }
      }
    });

    // Convert to array and sort by date
    const monthsArray = Object.entries(salesByMonth)
      .map(([month, data]) => ({
        month,
        sales_amount: data.amount,
        transactions_count: data.count,
      }))
      .sort((a, b) => new Date(a.month).getTime() - new Date(b.month).getTime());

    setMonthlySales(monthsArray);
    setYtdTotal(ytd);
  };

  if (loading) {
    return <div className="p-4 text-gray-500">Loading sales analysis...</div>;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Sales Analysis</h3>

      {/* YTD Summary */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 p-4 rounded-lg border border-indigo-200">
          <p className="text-xs text-indigo-700 font-medium">Year-to-Date Sales</p>
          <p className="text-2xl font-bold text-indigo-900">R{ytdTotal.toFixed(2)}</p>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
          <p className="text-xs text-purple-700 font-medium">Total Transactions</p>
          <p className="text-2xl font-bold text-purple-900">{monthlySales.reduce((sum, m) => sum + m.transactions_count, 0)}</p>
        </div>
      </div>

      {/* Monthly Breakdown */}
      {monthlySales.length > 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100 border-b border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Month</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Sales (R)</th>
                  <th className="px-4 py-3 text-center font-semibold text-gray-700">Transactions</th>
                </tr>
              </thead>
              <tbody>
                {monthlySales.map((month, idx) => (
                  <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-900">{month.month}</td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">
                      R{month.sales_amount.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-center text-gray-600">
                      {month.transactions_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center text-gray-600">
          No sales transactions recorded for this debtor in the current year
        </div>
      )}
    </div>
  );
}

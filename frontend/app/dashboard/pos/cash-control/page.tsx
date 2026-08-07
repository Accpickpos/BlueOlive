'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  TrendingUp,
  AlertCircle,
  Clock,
} from 'lucide-react';

interface CashControlSummary {
  control_date: string;
  total_sales: number;
  total_refunds: number;
  total_receipts: number;
  total_payouts: number;
  total_credits: number;
  total_cashed_cheques: number;
  total_new_laybyes: number;
  total_laybye_receipts: number;
  total_cancelled_laybyes: number;
  cash_expected: number;
  cash_takings: number;
  cheque_takings: number;
  speedpoint_takings: number;
}

export default function CashControlPage() {
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [controlDate, setControlDate] = useState(new Date().toISOString().split('T')[0]);
  const [summary, setSummary] = useState<CashControlSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading) fetchCashControl();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, controlDate]);

  const fetchCashControl = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await posAPI.getCashControlDailySummary({
        date: controlDate,
        cashier: user?.id,
      });
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cash control');
      setSummary(null);
    } finally {
      setLoading(false);
    }
  };

  const num = (v: number | undefined) => (v || 0).toFixed(2);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cash Control</h1>
          <p className="text-sm text-gray-500">Daily till reconciliation for {user?.username || 'the current cashier'}</p>
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Date</label>
          <Input type="date" value={controlDate} onChange={(e) => setControlDate(e.target.value)} />
        </div>
      </div>

      <div className="p-6 space-y-6">
        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6 flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <p className="text-red-800">{error}</p>
            </CardContent>
          </Card>
        )}

        {loading ? (
          <p className="text-gray-600">Loading cash control...</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  Cash Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Cash Sales</span>
                  <span className="font-bold">R{num(summary?.total_sales)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Receipts on Account</span>
                  <span className="font-bold">R{num(summary?.total_receipts)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">New Laybyes (Deposits)</span>
                  <span className="font-bold">R{num(summary?.total_new_laybyes)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Laybye Receipts</span>
                  <span className="font-bold">R{num(summary?.total_laybye_receipts)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Cash Refunds</span>
                  <span className="font-bold text-red-600">-R{num(summary?.total_refunds)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Credit Notes</span>
                  <span className="font-bold text-red-600">-R{num(summary?.total_credits)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Payouts</span>
                  <span className="font-bold text-red-600">-R{num(summary?.total_payouts)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Cashed Cheques</span>
                  <span className="font-bold text-red-600">-R{num(summary?.total_cashed_cheques)}</span>
                </div>
                <div className="border-t pt-3">
                  <div className="flex justify-between items-center">
                    <span className="font-bold">Expected Cash</span>
                    <span className="text-xl font-bold text-blue-900">R{num(summary?.cash_expected)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-purple-600" />
                  Takings By Tender
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Cash</span>
                  <span className="font-bold">R{num(summary?.cash_takings)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Cheque</span>
                  <span className="font-bold">R{num(summary?.cheque_takings)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Speedpoint / Card</span>
                  <span className="font-bold">R{num(summary?.speedpoint_takings)}</span>
                </div>
                <div className="text-center pt-6 text-sm text-gray-500">
                  Hourly breakdown not yet available
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

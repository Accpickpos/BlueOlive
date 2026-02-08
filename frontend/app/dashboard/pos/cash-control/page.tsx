'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  PlusCircle,
  TrendingUp,
  AlertCircle,
  Clock,
} from 'lucide-react';

export default function CashControlPage() {
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [cashier, setCashier] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCashControl();
  }, []);

  const fetchCashControl = async () => {
    setLoading(true);
    try {
      // API call would go here
      // const response = await posAPI.cashControl.getCurrentSession();
      // For now, show demo data
      setTimeout(() => {
        setCashier({
          name: 'John Doe',
          station: 'POS 1',
          start_time: new Date(Date.now() - 3600000).toISOString(),
          opening_balance: 500.00,
        });
        setSummary({
          cash_sales: 2500.00,
          cash_receipts: 1200.00,
          payouts: 300.00,
          expected_cash: 3900.00,
        });
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cash control');
    } finally {
      // Delay to simulate loading
      setTimeout(() => setLoading(false), 600);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Loading cash control...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">Cash Control</h1>
        <p className="text-sm text-gray-500">Cashier station enquiry, hourly analysis, payouts tracking</p>
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

        {/* Cashier Info */}
        <Card>
          <CardHeader>
            <CardTitle>Current Cashier Session</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {cashier ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Cashier</p>
                    <p className="text-lg font-bold">{cashier.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Station</p>
                    <p className="text-lg font-bold">{cashier.station}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Session Started</p>
                    <p className="text-lg font-bold">{new Date(cashier.start_time).toLocaleTimeString()}</p>
                  </div>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <p className="text-sm text-gray-600 mb-1">Opening Balance</p>
                  <p className="text-3xl font-bold text-blue-900">R{cashier.opening_balance?.toFixed(2) || '0.00'}</p>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600 mb-4">No active cashier session</p>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  <PlusCircle className="w-4 h-4 mr-2" />
                  Start Session
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Cash Summary */}
        {summary && (
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
                  <span className="font-bold">R{summary.cash_sales?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Cash Receipts</span>
                  <span className="font-bold">R{summary.cash_receipts?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Payouts</span>
                  <span className="font-bold text-red-600">-R{summary.payouts?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="border-t pt-3">
                  <div className="flex justify-between items-center">
                    <span className="font-bold">Expected Cash</span>
                    <span className="text-xl font-bold text-blue-900">R{summary.expected_cash?.toFixed(2) || '0.00'}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-purple-600" />
                  Hourly Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-center py-8">
                  <p className="text-gray-600 mb-4">Hourly breakdown not yet available</p>
                  <Button variant="outline">View Hourly Reports</Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4 justify-end">
          <Button variant="outline">Suspend Session</Button>
          <Button variant="outline" className="border-red-300 text-red-600 hover:bg-red-50">Close Session</Button>
        </div>
      </div>
    </div>
  );
}

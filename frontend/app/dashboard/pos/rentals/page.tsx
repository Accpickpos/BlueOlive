'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/useAuth';
import { rentalsApi, RentalTransaction } from '@/lib/rentalsApi';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { PlusCircle, AlertCircle, AlertTriangle } from 'lucide-react';

export default function RentalsPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [rentals, setRentals] = useState<RentalTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'OPEN' | 'RETURNED' | 'all'>('OPEN');

  useEffect(() => {
    if (!authLoading && user) {
      fetchRentals();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading, statusFilter]);

  const fetchRentals = async () => {
    setLoading(true);
    try {
      const params = statusFilter === 'all' ? undefined : { status: statusFilter };
      const response = await rentalsApi.list(params);
      setRentals(response.results || []);
    } catch (error) {
      console.error('Error fetching rentals:', error);
      setRentals([]);
    } finally {
      setLoading(false);
    }
  };

  // Outstanding Deposits summary (T8) — computed client-side from the OPEN
  // list already being fetched, so no separate report endpoint round-trip.
  const openRentals = rentals.filter((r) => r.status === 'OPEN');
  const totalLiability = openRentals.reduce((sum, r) => sum + Number(r.deposit_amount || 0), 0);
  const overdueCount = openRentals.filter((r) => r.is_overdue).length;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">LPG Cylinder Rentals</h1>
            <p className="text-sm text-gray-500">Cylinder deposits held, returns, and reconciliation</p>
          </div>
          <Link
            href="/dashboard/pos/rentals/checkout"
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            New Checkout
          </Link>
        </div>
      </div>

      {/* Outstanding Deposits summary (T8) */}
      {statusFilter !== 'RETURNED' && (
        <div className="px-6 py-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-gray-500">Total Deposit Liability Outstanding</p>
              <p className="text-2xl font-bold text-gray-900">R{totalLiability.toFixed(2)}</p>
              <p className="text-xs text-gray-400 mt-1">
                {openRentals.length === 0
                  ? 'No outstanding deposits.'
                  : `${openRentals.length} open rental${openRentals.length === 1 ? '' : 's'}`}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-gray-500">Overdue Rentals</p>
              <p className={`text-2xl font-bold ${overdueCount > 0 ? 'text-amber-600' : 'text-gray-900'}`}>
                {overdueCount}
              </p>
              <p className="text-xs text-gray-400 mt-1">Past the configured overdue threshold</p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="bg-white border-b px-6 py-4">
        <div className="flex gap-2">
          {(['OPEN', 'RETURNED', 'all'] as const).map((s) => (
            <Button
              key={s}
              variant={statusFilter === s ? 'default' : 'outline'}
              onClick={() => setStatusFilter(s)}
              size="sm"
            >
              {s === 'all' ? 'All' : s === 'OPEN' ? 'Open' : 'Returned'}
            </Button>
          ))}
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">Loading rentals...</p>
          </div>
        ) : rentals.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-4">
                  {statusFilter === 'OPEN' ? 'No outstanding deposits.' : 'No rentals found'}
                </p>
                <Link href="/dashboard/pos/rentals/checkout">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <PlusCircle className="w-4 h-4 mr-2" />
                    New Checkout
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer</TableHead>
                    <TableHead>Item</TableHead>
                    <TableHead className="text-right">Qty</TableHead>
                    <TableHead className="text-right">Deposit</TableHead>
                    <TableHead>Checkout Date</TableHead>
                    <TableHead>Due Date</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rentals.map((rental) => (
                    <TableRow key={rental.id}>
                      <TableCell className="font-medium">
                        <Link
                          href={`/dashboard/pos/rentals/${rental.id}`}
                          className="text-blue-600 hover:text-blue-700"
                        >
                          {rental.debtor_name}
                        </Link>
                      </TableCell>
                      <TableCell>{rental.stock_item_description}</TableCell>
                      <TableCell className="text-right">{rental.quantity}</TableCell>
                      <TableCell className="text-right font-medium">
                        R{Number(rental.deposit_amount).toFixed(2)}
                      </TableCell>
                      <TableCell>{new Date(rental.checkout_date).toLocaleDateString()}</TableCell>
                      <TableCell>{new Date(rental.due_date).toLocaleDateString()}</TableCell>
                      <TableCell>
                        {rental.status === 'OPEN' ? (
                          rental.is_overdue ? (
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-800">
                              <AlertTriangle className="w-3 h-3" />
                              Overdue
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                              Open
                            </span>
                          )
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            {rental.reconciliation_state?.replace(/_/g, ' ') || 'Returned'}
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

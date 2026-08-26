'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { gasApi, RentalTransaction, ReconciliationState } from '@/lib/gasApi';
import { getApiErrorMessage } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle, AlertTriangle, Loader2 } from 'lucide-react';

const RECONCILIATION_OPTIONS: { value: ReconciliationState; label: string; note: string }[] = [
  { value: 'REFUNDED', label: 'Refunded', note: 'Cylinder returned in good condition — deposit paid back.' },
  { value: 'BILLED_FOR_REPLACEMENT', label: 'Billed for Replacement', note: 'Cylinder lost or damaged — customer charged (VAT applies).' },
  { value: 'WRITTEN_OFF', label: 'Written Off', note: 'Deposit forfeited. Requires Accountant/Admin.' },
  { value: 'DISPUTED', label: 'Disputed', note: 'Flag for investigation — no money moves yet. Requires Accountant/Admin.' },
];

export default function GasDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [rental, setRental] = useState<RentalTransaction | null>(null);
  const [loading, setLoading] = useState(true);
  const [reconciling, setReconciling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedState, setSelectedState] = useState<ReconciliationState>('REFUNDED');
  const [replacementPrice, setReplacementPrice] = useState('');

  useEffect(() => {
    fetchRental();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const fetchRental = async () => {
    setLoading(true);
    try {
      const data = await gasApi.get(id);
      setRental(data);
    } catch (err) {
      console.error('Error fetching rental:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReturn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (selectedState === 'BILLED_FOR_REPLACEMENT' && !replacementPrice) {
      setError('Enter the replacement unit price');
      return;
    }

    setReconciling(true);
    try {
      const updated = await gasApi.returnCylinder(id, {
        reconciliation_state: selectedState,
        replacement_unit_price:
          selectedState === 'BILLED_FOR_REPLACEMENT' ? Number(replacementPrice) : undefined,
      });
      setRental(updated);
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setError(
          "You don't have permission to write off or dispute a deposit — this requires an Accountant or Admin role."
        );
      } else {
        setError(getApiErrorMessage(err, 'Return failed — please try again.'));
      }
    } finally {
      setReconciling(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!rental) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <Card>
          <CardContent className="py-8 text-center text-gray-600">
            No matching rental found.
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">Rental #{rental.id}</h1>
        <p className="text-sm text-gray-500">{rental.debtor_name} — {rental.stock_item_description}</p>
      </div>

      <div className="p-6 max-w-2xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Details</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Quantity</p>
              <p className="font-medium">{rental.quantity}</p>
            </div>
            <div>
              <p className="text-gray-500">Deposit Amount</p>
              <p className="font-medium">R{Number(rental.deposit_amount).toFixed(2)}</p>
            </div>
            <div>
              <p className="text-gray-500">Checkout Date</p>
              <p className="font-medium">{new Date(rental.checkout_date).toLocaleDateString()}</p>
            </div>
            <div>
              <p className="text-gray-500">Due Date</p>
              <p className="font-medium">
                {new Date(rental.due_date).toLocaleDateString()}
                {rental.status === 'OPEN' && rental.is_overdue && (
                  <span className="ml-2 inline-flex items-center gap-1 text-amber-700">
                    <AlertTriangle className="w-3 h-3" /> Overdue
                  </span>
                )}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Status</p>
              <p className="font-medium">{rental.status}</p>
            </div>
            {rental.status === 'RETURNED' && (
              <div>
                <p className="text-gray-500">Reconciliation</p>
                <p className="font-medium">{rental.reconciliation_state?.replace(/_/g, ' ')}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {rental.status === 'OPEN' ? (
          <Card>
            <CardHeader>
              <CardTitle>Return / Reconcile</CardTitle>
            </CardHeader>
            <CardContent>
              {error && (
                <div className="mb-4 flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">
                  <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleReturn} className="space-y-4">
                <div>
                  <Label className="mb-2 block">Outcome</Label>
                  <div className="space-y-2">
                    {RECONCILIATION_OPTIONS.map((opt) => (
                      <label
                        key={opt.value}
                        className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer ${
                          selectedState === opt.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                        }`}
                      >
                        <input
                          type="radio"
                          name="reconciliation_state"
                          value={opt.value}
                          checked={selectedState === opt.value}
                          onChange={() => setSelectedState(opt.value)}
                          className="mt-1"
                        />
                        <div>
                          <p className="font-medium text-gray-900">{opt.label}</p>
                          <p className="text-xs text-gray-500">{opt.note}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {selectedState === 'BILLED_FOR_REPLACEMENT' && (
                  <div>
                    <Label htmlFor="replacement_price" className="mb-1 block">
                      Replacement Unit Price (excl. VAT)
                    </Label>
                    <Input
                      id="replacement_price"
                      type="number"
                      min="0"
                      step="0.01"
                      value={replacementPrice}
                      onChange={(e) => setReplacementPrice(e.target.value)}
                      disabled={reconciling}
                    />
                    <p className="text-xs text-gray-500 mt-1">14% VAT is calculated automatically.</p>
                  </div>
                )}

                <div className="flex justify-end pt-2">
                  <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={reconciling}>
                    {reconciling ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      'Confirm Return'
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        ) : (
          <div className="text-sm text-gray-500 text-center py-4">
            This rental was reconciled on{' '}
            {rental.returned_date && new Date(rental.returned_date).toLocaleDateString()}.
          </div>
        )}

        <Button type="button" variant="outline" onClick={() => router.push('/dashboard/gas')}>
          Back to Gas
        </Button>
      </div>
    </div>
  );
}

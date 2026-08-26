'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { gasApi } from '@/lib/gasApi';
import { getApiErrorMessage } from '@/lib/api';
import { DebtorPicker } from '@/components/pos/DebtorPicker';
import { StockItemPicker } from '@/components/pos/StockItemPicker';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle, Loader2 } from 'lucide-react';

export default function GasCheckoutPage() {
  const { user } = useAuth();
  const router = useRouter();

  const [debtor, setDebtor] = useState<{ account_number: string; name: string } | null>(null);
  const [stockItem, setStockItem] = useState<{ stock_code: string; description: string } | null>(null);
  const [quantity, setQuantity] = useState('1');
  const [depositAmount, setDepositAmount] = useState('');
  const [reference, setReference] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!debtor) {
      setError('Select a customer');
      return;
    }
    if (!stockItem) {
      setError('Select the cylinder stock item');
      return;
    }
    const qty = Number(quantity);
    const deposit = Number(depositAmount);
    if (!qty || qty <= 0) {
      setError('Quantity must be greater than zero');
      return;
    }
    if (!deposit || deposit < 0) {
      setError('Enter the deposit amount held');
      return;
    }

    setLoading(true);
    try {
      const debtorId = parseInt(debtor.account_number, 10);
      const rental = await gasApi.checkout({
        debtor: debtorId,
        stock_item: stockItem.stock_code,
        quantity: qty,
        deposit_amount: deposit,
        reference: reference || undefined,
      });
      router.push(`/dashboard/gas/${rental.id}`);
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Checkout failed — please check stock availability and try again.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">Cylinder Checkout</h1>
        <p className="text-sm text-gray-500">Check a cylinder out to a customer against a held deposit</p>
      </div>

      <div className="p-6 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>Checkout Details</CardTitle>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="mb-4 flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label className="mb-1 block">Customer</Label>
                <DebtorPicker
                  onSelect={(d) => setDebtor({ account_number: d.account_number, name: d.name })}
                  placeholder={debtor ? debtor.name : 'Search customers...'}
                  disabled={loading}
                />
              </div>

              <div>
                <Label className="mb-1 block">Cylinder</Label>
                <StockItemPicker
                  onSelect={(item) =>
                    setStockItem({ stock_code: item.stock_code, description: item.description })
                  }
                  placeholder={stockItem ? stockItem.description : 'Search stock items...'}
                  disabled={loading}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="quantity" className="mb-1 block">Quantity</Label>
                  <Input
                    id="quantity"
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    disabled={loading}
                  />
                </div>
                <div>
                  <Label htmlFor="deposit" className="mb-1 block">Deposit Amount (R)</Label>
                  <Input
                    id="deposit"
                    type="number"
                    min="0"
                    step="0.01"
                    value={depositAmount}
                    onChange={(e) => setDepositAmount(e.target.value)}
                    disabled={loading}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="reference" className="mb-1 block">Reference (optional)</Label>
                <Input
                  id="reference"
                  value={reference}
                  onChange={(e) => setReference(e.target.value)}
                  disabled={loading}
                  maxLength={10}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => router.back()} disabled={loading}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    'Complete Checkout'
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

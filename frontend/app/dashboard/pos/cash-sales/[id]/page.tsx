'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { useRouter, useParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, ArrowLeft, Printer } from 'lucide-react';

export default function CashSaleDetailPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  
  const [sale, setSale] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSale = async () => {
      if (!params.id || authLoading || !user) return;
      
      try {
        setLoading(true);
        const data = await posAPI.getCashSale(params.id as string);
        setSale(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load cash sale');
      } finally {
        setLoading(false);
      }
    };

    fetchSale();
  }, [params.id, posAPI, authLoading, user]);

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
        <Button onClick={() => router.back()} className="mt-4">
          Go Back
        </Button>
      </div>
    );
  }

  if (!sale) {
    return (
      <div className="p-8">
        <p>No sale found</p>
        <Button onClick={() => router.push('/dashboard/pos/cash-sales')}>
          Back to List
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Button variant="outline" size="icon" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Cash Sale</h1>
              <p className="text-gray-600">
                Sale #{sale.sale_number || sale.id}
              </p>
            </div>
          </div>
          <Button variant="outline">
            <Printer className="h-4 w-4 mr-2" />
            Print
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Sale Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Date</p>
                <p className="font-medium">{sale.sale_date}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Sale Number</p>
                <p className="font-medium">{sale.sale_number}</p>
              </div>
              {sale.customer_name && (
                <div>
                  <p className="text-sm text-gray-600">Customer</p>
                  <p className="font-medium">{sale.customer_name}</p>
                </div>
              )}
              {sale.cashier_name && (
                <div>
                  <p className="text-sm text-gray-600">Cashier</p>
                  <p className="font-medium">{sale.cashier_name}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {sale.lines && sale.lines.length > 0 && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Line Items</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Item</th>
                    <th className="text-right py-2">Qty</th>
                    <th className="text-right py-2">Price</th>
                    <th className="text-right py-2">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {sale.lines.map((line: any, index: number) => (
                    <tr key={index} className="border-b">
                      <td className="py-2">
                        <p className="font-medium">{line.description}</p>
                        <p className="text-sm text-gray-500">{line.stock_code}</p>
                      </td>
                      <td className="text-right py-2">{line.quantity}</td>
                      <td className="text-right py-2">R{Number(line.unit_price || 0).toFixed(2)}</td>
                      <td className="text-right py-2">R{Number(line.line_total || 0).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}

        {sale.tenders && sale.tenders.length > 0 && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Payments</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {sale.tenders.map((tender: any, index: number) => (
                  <div key={index} className="flex justify-between">
                    <span>{tender.tender_type}</span>
                    <span className="font-medium">R{Number(tender.amount || 0).toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <div className="mt-6 flex justify-end">
          <Card className="w-64">
            <CardContent className="pt-6">
              <div className="flex justify-between mb-2">
                <span>Subtotal:</span>
                <span>R{Number(sale.subtotal || 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between mb-2">
                <span>VAT:</span>
                <span>R{Number(sale.vat_amount || 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-bold text-lg">
                <span>Total:</span>
                <span>R{Number(sale.total_amount || 0).toFixed(2)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

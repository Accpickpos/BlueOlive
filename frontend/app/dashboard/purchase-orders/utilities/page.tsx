'use client';

import React, { useState } from 'react';
import { ArrowLeft, AlertTriangle, CheckCircle, Loader } from 'lucide-react';
import Link from 'next/link';
import purchaseOrdersApi from '@/lib/purchaseOrdersApi';
import { getApiErrorMessage } from '@/lib/api';

export default function UtilitiesPage() {
  const [resetting, setResetting] = useState(false);
  const [resetResult, setResetResult] = useState<{ items_updated: number; changes: any[] } | null>(null);
  const [error, setError] = useState('');

  const handleResetQuantities = async () => {
    if (
      !window.confirm(
        "This recomputes every stock item's quantity-on-order from actual outstanding purchase orders. Continue?"
      )
    ) {
      return;
    }

    setResetting(true);
    setError('');
    try {
      const result = await purchaseOrdersApi.utilities.resyncOnOrderQuantities();
      setResetResult(result as any);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to resync on-order quantities'));
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <Link
          href="/dashboard/purchase-orders"
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Purchase Orders
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">
          Purchase Order Utilities
        </h1>
        <p className="text-sm text-gray-500">
          Maintenance and administrative tools
        </p>
      </div>

      <div className="p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <span className="text-red-600">{error}</span>
            </div>
          )}

          {/* Reset Purchase Order Quantities Utility */}
          <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b bg-gray-50">
              <h2 className="text-lg font-semibold text-gray-900">
                Reset Purchase Order Quantities
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Resync stock-on-order quantities against actual outstanding purchase orders
              </p>
            </div>

            <div className="px-6 py-6">
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-900 mb-2">
                    What this does:
                  </h3>
                  <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                    <li>Recomputes each stock item's "quantity on order" from outstanding PO lines</li>
                    <li>Fixes drift caused by bugs, manual edits, or partial failures</li>
                    <li>Safe to run at any time — it only corrects quantity_on_order, nothing else</li>
                    <li>Requires Admin access</li>
                  </ul>
                </div>

                {resetResult ? (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="font-medium text-green-900">Resync complete</h4>
                        <p className="text-sm text-green-700 mt-1">
                          {resetResult.items_updated} stock item{resetResult.items_updated === 1 ? '' : 's'} corrected
                        </p>
                        {resetResult.changes?.length > 0 && (
                          <div className="mt-3 max-h-48 overflow-y-auto border border-green-200 rounded bg-white">
                            <table className="w-full text-xs">
                              <thead className="bg-green-100">
                                <tr>
                                  <th className="text-left px-2 py-1">Stock Code</th>
                                  <th className="text-right px-2 py-1">Was</th>
                                  <th className="text-right px-2 py-1">Now</th>
                                </tr>
                              </thead>
                              <tbody>
                                {resetResult.changes.map((c: any, i: number) => (
                                  <tr key={i} className="border-t border-green-100">
                                    <td className="px-2 py-1">{c.stock_code}</td>
                                    <td className="px-2 py-1 text-right">{c.previous_quantity_on_order}</td>
                                    <td className="px-2 py-1 text-right">{c.corrected_quantity_on_order}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">
                    Click the button below to resync stock-on-order quantities.
                  </p>
                )}
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={handleResetQuantities}
                  disabled={resetting}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {resetting ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Resyncing...
                    </>
                  ) : (
                    'Resync Quantities'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

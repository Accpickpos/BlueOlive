'use client';

import React, { useState } from 'react';
import { ArrowLeft, AlertTriangle, CheckCircle, Loader } from 'lucide-react';
import Link from 'next/link';
import purchaseOrdersApi from '@/lib/purchaseOrdersApi';

export default function UtilitiesPage() {
  const [indexing, setIndexing] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [indexResult, setIndexResult] = useState<any>(null);
  const [resetResult, setResetResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleIndexFiles = async () => {
    setIndexing(true);
    setError('');
    try {
      const result = await purchaseOrdersApi.utilities.indexFiles();
      setIndexResult(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to index files'
      );
    } finally {
      setIndexing(false);
    }
  };

  const handleResetQuantities = async () => {
    if (
      !window.confirm(
        'Are you sure? This will reset all purchase order quantities. This action cannot be undone.'
      )
    ) {
      return;
    }

    setResetting(true);
    setError('');
    try {
      const result = await purchaseOrdersApi.utilities.resetQuantities();
      setResetResult(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to reset quantities'
      );
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

          {/* Index Files Utility */}
          <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b bg-gray-50">
              <h2 className="text-lg font-semibold text-gray-900">
                Index Files
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Rebuild the file index for optimized search performance
              </p>
            </div>

            <div className="px-6 py-6">
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-900 mb-2">
                    What this does:
                  </h3>
                  <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                    <li>Rebuilds all purchase order file indices</li>
                    <li>Optimizes search and filter performance</li>
                    <li>Ensures data consistency</li>
                    <li>
                      Resolves any corrupted or missing index entries
                    </li>
                  </ul>
                </div>

                {indexResult ? (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-green-900">
                          {indexResult.message}
                        </h4>
                        <p className="text-sm text-green-700 mt-1">
                          Files reindexed: {indexResult.files_reindexed}
                        </p>
                        {indexResult.reindex_time_ms && (
                          <p className="text-xs text-green-600 mt-1">
                            Time taken: {indexResult.reindex_time_ms}ms
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">
                    Click the button below to rebuild the file index.
                    This may take several minutes depending on the number
                    of files.
                  </p>
                )}
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={handleIndexFiles}
                  disabled={indexing}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {indexing ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Indexing...
                    </>
                  ) : (
                    'Start Indexing'
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Reset Quantities Utility */}
          <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b bg-gray-50">
              <h2 className="text-lg font-semibold text-gray-900">
                Reset Quantities
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Reset all purchase order quantities to default values
              </p>
            </div>

            <div className="px-6 py-6">
              <div className="space-y-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h3 className="font-medium text-red-900 mb-2">
                    Warning: This action is permanent
                  </h3>
                  <ul className="text-sm text-red-800 space-y-1 list-disc list-inside">
                    <li>All purchase order quantities will be reset</li>
                    <li>
                      Historical data will be permanently altered
                    </li>
                    <li>This action cannot be undone</li>
                    <li>
                      Backup your database before proceeding
                    </li>
                  </ul>
                </div>

                {resetResult ? (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-green-900">
                          {resetResult.message}
                        </h4>
                        <p className="text-sm text-green-700 mt-1">
                          Items reset: {resetResult.items_reset}
                        </p>
                        {resetResult.reset_time_ms && (
                          <p className="text-xs text-green-600 mt-1">
                            Time taken: {resetResult.reset_time_ms}ms
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">
                    Only click this button if you understand the consequences.
                    Make sure to backup your database first.
                  </p>
                )}
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={handleResetQuantities}
                  disabled={resetting}
                  className="flex items-center gap-2 px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {resetting ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Resetting...
                    </>
                  ) : (
                    'Reset All Quantities'
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* System Information */}
          <div className="bg-white rounded-lg border shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              System Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Last Index Date</p>
                <p className="font-medium text-gray-900">
                  {indexResult?.generated_at
                    ? new Date(
                        indexResult.generated_at
                      ).toLocaleDateString('en-ZA')
                    : 'Not available'}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Last Reset Date</p>
                <p className="font-medium text-gray-900">
                  {resetResult?.generated_at
                    ? new Date(
                        resetResult.generated_at
                      ).toLocaleDateString('en-ZA')
                    : 'Not available'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import { apiRequest } from '@/lib/api';

interface ConvertCategoryModalProps {
  isOpen: boolean;
  debtorId: number;
  debtorName: string;
  currentCategory: string;
  onSuccess: (result: any) => void;
  onCancel: () => void;
}

export default function ConvertCategoryModal({
  isOpen,
  debtorId,
  debtorName,
  currentCategory,
  onSuccess,
  onCancel,
}: ConvertCategoryModalProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(undefined);
  const [preserveData, setPreserveData] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const categoryLabels: { [key: string]: string } = {
    '': 'Balance Brought Forward',
    'O': 'Open Item',
    'C': 'Cash Customer',
  };

  const categoryDescriptions: { [key: string]: string } = {
    '': 'Tracks balance by aging periods (current, 30, 60, 90+ days). Suitable for customers who pay on statement.',
    'O': 'Tracks individual invoices and their payment status. Suitable for customers who pay by invoice number.',
    'C': 'Cash customers. No credit terms. Requires cash or immediate payment.',
  };

  const handleConvert = async () => {
    if (selectedCategory === undefined || selectedCategory === null) {
      setError('Please select a target category');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await apiRequest(`/api/v1/debtors/${debtorId}/convert-category/`, {
        method: 'POST',
        body: {
          new_category: selectedCategory,
          preserve_data: preserveData,
        },
      });

      console.log('Conversion result:', result);
      onSuccess(result);
    } catch (err: any) {
      console.error('Conversion failed:', err);
      setError(err.message || 'Failed to convert account category');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  const options = ['', 'O', 'C'].filter((cat) => cat !== currentCategory);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4">
        {/* Header */}
        <div className="bg-blue-50 px-6 py-4 border-b border-blue-200">
          <h2 className="text-xl font-bold text-gray-900">Convert Account Category</h2>
          <p className="text-sm text-gray-600 mt-1">{debtorName}</p>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex gap-3">
              <div className="text-yellow-600 font-bold">⚠</div>
              <div>
                <p className="font-semibold text-yellow-900">Important</p>
                <p className="text-sm text-yellow-800 mt-1">
                  Converting between accounting methods will migrate your balance data to maintain accuracy.
                  This operation cannot be undone. Please ensure you have a backup.
                </p>
              </div>
            </div>
          </div>

          {/* Current Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Current Category
            </label>
            <div className="bg-gray-50 border border-gray-300 rounded px-3 py-2 text-gray-900 font-medium">
              {categoryLabels[currentCategory]}
            </div>
            <p className="text-xs text-gray-600 mt-2">{categoryDescriptions[currentCategory]}</p>
          </div>

          {/* Target Category Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Convert To (Required)
            </label>
            <div className="space-y-2">
              {options.map((category) => (
                <div key={category} className="relative">
                  <input
                    type="radio"
                    id={`category-${category}`}
                    name="category"
                    value={category}
                    checked={selectedCategory === category}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="peer sr-only"
                  />
                  <label
                    htmlFor={`category-${category}`}
                    className="flex items-start cursor-pointer p-3 border border-gray-200 rounded-lg peer-checked:border-blue-500 peer-checked:bg-blue-50 hover:bg-gray-50"
                  >
                    <input
                      type="radio"
                      name="category-radio"
                      checked={selectedCategory === category}
                      onChange={() => setSelectedCategory(category)}
                      className="mt-1 mr-3"
                      disabled
                    />
                    <div>
                      <p className="font-medium text-gray-900">{categoryLabels[category]}</p>
                      <p className="text-xs text-gray-600 mt-1">{categoryDescriptions[category]}</p>
                    </div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Data Migration Options */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-3">
            <p className="font-medium text-gray-900">Data Migration Options</p>

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={preserveData}
                onChange={(e) => setPreserveData(e.target.checked)}
                className="mt-1"
              />
              <div>
                <p className="font-medium text-gray-700">Preserve existing balance data</p>
                <p className="text-xs text-gray-600 mt-1">
                  {preserveData
                    ? 'Converting from Balance Forward will create transaction records from aging buckets. Converting from Open Item will aggregate transactions into aging buckets.'
                    : 'All balance data will be cleared. Only recommended if starting fresh.'}
                </p>
              </div>
            </label>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Migration Summary */}
          {selectedCategory && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="font-medium text-blue-900 mb-2">Migration Details</p>
              <ul className="text-sm text-blue-800 space-y-1">
                {selectedCategory === '' && currentCategory === 'O' && preserveData && (
                  <>
                    <li>✓ Outstanding transactions will be converted into balance aging buckets</li>
                    <li>✓ Transaction history will be preserved for reference</li>
                    <li>✓ Aging analysis will be based on transaction dates</li>
                  </>
                )}
                {selectedCategory === 'O' && currentCategory === '' && preserveData && (
                  <>
                    <li>✓ Current aging buckets will be converted to transaction records</li>
                    <li>✓ Each aging period will create a summarized debit journal entry</li>
                    <li>✓ Transactions will be marked as allocated</li>
                  </>
                )}
                {selectedCategory === 'C' && (
                  <>
                    <li>✓ Account type will be set to Cash Customer</li>
                    <li>✓ No credit terms will be allowed</li>
                    <li>✓ Requires cash or immediate payment for all transactions</li>
                  </>
                )}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleConvert}
            disabled={loading || selectedCategory === undefined || selectedCategory === null}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Converting...' : 'Convert Category'}
          </button>
        </div>
      </div>
    </div>
  );
}

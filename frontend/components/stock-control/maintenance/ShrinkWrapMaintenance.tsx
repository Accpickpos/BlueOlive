'use client';

import { ArrowLeft } from 'lucide-react';

interface ShrinkWrapMaintenanceProps {
  onBack: () => void;
}

export default function ShrinkWrapMaintenance({ onBack }: ShrinkWrapMaintenanceProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <h2 className="text-2xl font-bold text-gray-900">Shrink Wraps</h2>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-3">Overview</h3>
          <p className="text-sm text-blue-800 mb-3">Create relationships between bulk items and shrink-wrapped units. Example: A bulk pack of 48 Bic Pens relates to individual Bic Pens.</p>
          <div className="grid md:grid-cols-2 gap-3 mt-3">
            <div className="bg-white p-3 rounded border border-blue-200">
              <p className="text-xs font-semibold text-blue-700">Example:</p>
              <p className="text-xs text-blue-800">Bulk: 000-003 (Bic Pens 48Pack)</p>
              <p className="text-xs text-blue-800">Shrink: 000-005 (Bic Pens Single)</p>
              <p className="text-xs text-blue-800">Quantity: 48</p>
            </div>
          </div>
        </div>

        <div className="border-l-4 border-green-600 bg-gray-50 p-4">
          <h4 className="font-semibold text-gray-900 mb-2">Setup Steps</h4>
          <ol className="text-sm text-gray-700 space-y-2 list-decimal list-inside">
            <li>Enter the Shrink Pack Code or use search</li>
            <li>Enter the Bulk Pack Code or use search</li>
            <li>Enter the quantity of shrinks in the bulk</li>
            <li>Save the relationship</li>
          </ol>
        </div>

        <div className="border-l-4 border-orange-600 bg-gray-50 p-4">
          <h4 className="font-semibold text-gray-900 mb-2">Calculation Example</h4>
          <p className="text-sm text-gray-700 mb-2">To calculate the quantity to enter:</p>
          <p className="text-sm text-gray-700 font-mono bg-white p-2 rounded">Bulk Quantity ÷ Shrink Quantity = Result</p>
          <p className="text-sm text-gray-700 mt-2">Example: 48 ÷ 1 = 48</p>
        </div>

        <div className="border-l-4 border-purple-600 bg-gray-50 p-4">
          <h4 className="font-semibold text-gray-900 mb-2">Options</h4>
          <ul className="text-sm text-gray-700 space-y-1">
            <li>• Shrink Wraps Maintenance (Create/Update relationships)</li>
            <li>• View/Print Shrink Wrap Relationships</li>
          </ul>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-semibold text-yellow-900 mb-2">Important</h3>
          <p className="text-sm text-yellow-800">Stock codes must exist for both bulk and shrink units before creating the relationship.</p>
        </div>
      </div>
    </div>
  );
}
'use client';

import { ArrowLeft } from 'lucide-react';

interface OneTouchLookupKeyMaintenanceProps {
  onBack: () => void;
}

export default function OneTouchLookupKeyMaintenance({ onBack }: OneTouchLookupKeyMaintenanceProps) {
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
        <h2 className="text-2xl font-bold text-gray-900">One-Touch Look-Up Keys</h2>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-3">Setup Instructions</h3>
          <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
            <li>Press Shift + Alpha key (e.g., Shift+A for capital A)</li>
            <li>At the Stock Code prompt, enter the stock code or use search</li>
            <li>Click Yes to save the key mapping</li>
          </ol>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-900 mb-3">At Point of Sale</h3>
          <p className="text-sm text-green-800 mb-2">Instead of clicking INSERT, press your linked key:</p>
          <p className="text-sm text-green-800">• The stock details will be displayed automatically</p>
          <p className="text-sm text-green-800">• Continue entering transaction details</p>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h3 className="font-semibold text-purple-900 mb-3">View/Clear Settings</h3>
          <ul className="text-sm text-purple-800 space-y-1">
            <li>• Press [?] to display current alpha key settings</li>
            <li>• Press [-] to clear all alpha key settings</li>
          </ul>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-semibold text-yellow-900 mb-2">Note</h3>
          <p className="text-sm text-yellow-800">Use Capital Letters only. This is a customization feature for fast POS access.</p>
        </div>
      </div>
    </div>
  );
}
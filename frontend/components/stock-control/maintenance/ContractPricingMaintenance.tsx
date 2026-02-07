'use client';

import { ArrowLeft } from 'lucide-react';

interface ContractPricingMaintenanceProps {
  onBack: () => void;
}

export default function ContractPricingMaintenance({ onBack }: ContractPricingMaintenanceProps) {
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
        <h2 className="text-2xl font-bold text-gray-900">Contract Pricing</h2>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-3">Overview</h3>
          <p className="text-sm text-blue-800">Link debtors to contract prices on specific items, departments, or suppliers. Contract prices take priority over all master file and special deal pricing and are automatically displayed at POS.</p>
        </div>

        <div className="space-y-4">
          <div className="border-l-4 border-blue-600 bg-gray-50 p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Setup Process</h4>
            <ol className="text-sm text-gray-700 space-y-2 list-decimal list-inside">
              <li>Enter the Debtor's account number or use search facility</li>
              <li>Select whether Fixed Pricing is enabled</li>
              <li>Choose pricing method below</li>
            </ol>
          </div>

          <div className="border-l-4 border-green-600 bg-gray-50 p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Fixed Pricing</h4>
            <p className="text-sm text-gray-700">If Yes: POS cannot apply discounts outside contract pricing</p>
            <p className="text-sm text-gray-700">If No: POS can apply additional discounts</p>
          </div>

          <div className="border-l-4 border-purple-600 bg-gray-50 p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Pricing Methods</h4>
            <ul className="text-sm text-gray-700 space-y-2">
              <li><strong>Per Line Item (Specific Stock Code):</strong> Set actual price or calculate using cost + markup %</li>
              <li><strong>Department-based:</strong> Apply discount/markup % for selected departments</li>
              <li><strong>Supplier-based:</strong> Apply discount/markup % for sales from specific suppliers</li>
              <li><strong>Supplier + Department:</strong> Combine supplier and department for granular control</li>
            </ul>
          </div>

          <div className="border-l-4 border-orange-600 bg-gray-50 p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Options</h4>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• Adjust contract price</li>
              <li>• Print contract listing</li>
              <li>• Locate contract item by Code/Description</li>
              <li>• Delete contract price</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
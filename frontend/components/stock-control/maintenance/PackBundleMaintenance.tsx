'use client';

import { ArrowLeft } from 'lucide-react';

interface PackBundleMaintenanceProps {
  onBack: () => void;
}

export default function PackBundleMaintenance({ onBack }: PackBundleMaintenanceProps) {
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
        <h2 className="text-2xl font-bold text-gray-900">Packs / Bundles</h2>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-3">Overview</h3>
          <p className="text-sm text-blue-800 mb-3">Create finished products or recipes by grouping multiple stock items together. Any combination of stock items and quantities can form a finished product.</p>
          <p className="text-sm text-blue-800">Example: Ration Pack #1 containing multiple items</p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div className="border-l-4 border-green-600 bg-gray-50 p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Step 1: Create Stock Code</h4>
            <ol className="text-sm text-gray-700 space-y-2 list-decimal list-inside">
              <li>Enter stock code for the finished product</li>
              <li>Enter description (e.g., "Ration Pack #1")</li>
              <li>Select department</li>
              <li>Select tax code</li>
              <li>Set default selling quantity</li>
              <li>Select supplier (usually "Internal")</li>
              <li>Set negative quantity setting</li>
              <li>Set maximum discount % if needed</li>
            </ol>
          </div>

          <div className="border-l-4 border-purple-600 bg-gray-50 p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Step 2: Ingredient Maintenance</h4>
            <ol className="text-sm text-gray-700 space-y-2 list-decimal list-inside">
              <li>Insert stock item codes (ingredients)</li>
              <li>Enter stock description</li>
              <li>Enter quantity of each ingredient</li>
              <li>System displays ingredient values and total cost</li>
              <li>End ingredient maintenance</li>
              <li>Set markup % and selling price</li>
              <li>Save the bundle</li>
            </ol>
          </div>
        </div>

        <div className="border-l-4 border-orange-600 bg-gray-50 p-4">
          <h4 className="font-semibold text-gray-900 mb-2">Options</h4>
          <ul className="text-sm text-gray-700 space-y-1">
            <li>• Packs/Bundles Maintenance (Create/Update)</li>
            <li>• View Compositions of Packs/Bundles</li>
            <li>• Composition - View ingredients and costs</li>
          </ul>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-semibold text-yellow-900 mb-2">Important Notes</h3>
          <ul className="text-sm text-yellow-800 space-y-1">
            <li>• All ingredient stock codes must exist before creating the bundle</li>
            <li>• Create a supplier called "Internal" in Creditors before setup</li>
            <li>• System automatically calculates total cost of the bundle</li>
            <li>• You can use any combination of stock items</li>
          </ul>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-900 mb-2">See Also</h3>
          <p className="text-sm text-green-800">For creation and updating of finished goods, refer to Manufacture Items section</p>
        </div>
      </div>
    </div>
  );
}
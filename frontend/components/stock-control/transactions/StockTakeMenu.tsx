'use client';

import { useState } from 'react';
import { ArrowLeft, FileText, Barcode, TrendingDown, Calculator, BarChart3, Wrench } from 'lucide-react';
import PrintStockTakeForms from './stock-take/PrintStockTakeForms';
import StockCount from './stock-take/StockCount';
import VarianceReport from './stock-take/VarianceReport';
import StockValuation from './stock-take/StockValuation';
import StockTakeUpdate from './stock-take/StockTakeUpdate';
import StockAdjustments from './stock-take/StockAdjustments';

interface StockTakeMenuProps {
  onBack: () => void;
}

type StockTakeOption =
  | 'menu'
  | 'print-forms'
  | 'count'
  | 'variance'
  | 'valuation'
  | 'update'
  | 'adjustments';

export default function StockTakeMenu({ onBack }: StockTakeMenuProps) {
  const [currentOption, setCurrentOption] = useState<StockTakeOption>('menu');

  const handleBack = () => {
    if (currentOption === 'menu') {
      onBack();
    } else {
      setCurrentOption('menu');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          <ArrowLeft size={20} />
          Back
        </button>
        <h2 className="text-2xl font-bold">Stock Take</h2>
      </div>

      {currentOption === 'menu' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Print Stock Take Forms */}
          <button
            onClick={() => setCurrentOption('print-forms')}
            className="p-6 bg-white border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition text-left"
          >
            <div className="flex items-start gap-4">
              <FileText className="text-blue-600" size={32} />
              <div>
                <h3 className="text-xl font-semibold mb-2">A. Print Stock Take Forms</h3>
                <p className="text-gray-600 text-sm mb-3">
                  Generate stock take forms for physical counting. Select sort order and filtering options.
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Choose sort order (by department, supplier, code, description, bin)</li>
                  <li>• Filter by department or status</li>
                  <li>• Generate forms for staff</li>
                </ul>
              </div>
            </div>
          </button>

          {/* Stock Count */}
          <button
            onClick={() => setCurrentOption('count')}
            className="p-6 bg-white border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition text-left"
          >
            <div className="flex items-start gap-4">
              <Barcode className="text-green-600" size={32} />
              <div>
                <h3 className="text-xl font-semibold mb-2">B. Stock Count</h3>
                <p className="text-gray-600 text-sm mb-3">
                  Enter quantities counted for each stock item during physical count.
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Navigate through items</li>
                  <li>• Enter quantities counted</li>
                  <li>• Support for multiple locations</li>
                </ul>
              </div>
            </div>
          </button>

          {/* Stock Variance Report */}
          <button
            onClick={() => setCurrentOption('variance')}
            className="p-6 bg-white border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition text-left"
          >
            <div className="flex items-start gap-4">
              <TrendingDown className="text-orange-600" size={32} />
              <div>
                <h3 className="text-xl font-semibold mb-2">C. Stock Variance Report</h3>
                <p className="text-gray-600 text-sm mb-3">
                  Review discrepancies between counted and system quantities.
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Identify variances</li>
                  <li>• View variance quantities and values</li>
                  <li>• Make correcting adjustments</li>
                </ul>
              </div>
            </div>
          </button>

          {/* Stock Valuation */}
          <button
            onClick={() => setCurrentOption('valuation')}
            className="p-6 bg-white border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition text-left"
          >
            <div className="flex items-start gap-4">
              <Calculator className="text-purple-600" size={32} />
              <div>
                <h3 className="text-xl font-semibold mb-2">D. Stock Valuation Report</h3>
                <p className="text-gray-600 text-sm mb-3">
                  Print valuation of quantity counted (useful before stock take update).
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Actual quantity on hand valuation</li>
                  <li>• Quantity counted valuation</li>
                  <li>• Print before after-trading update</li>
                </ul>
              </div>
            </div>
          </button>

          {/* Stock Take Update */}
          <button
            onClick={() => setCurrentOption('update')}
            className="p-6 bg-white border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition text-left"
          >
            <div className="flex items-start gap-4">
              <BarChart3 className="text-red-600" size={32} />
              <div>
                <h3 className="text-xl font-semibold mb-2">F. Stock Take Update</h3>
                <p className="text-gray-600 text-sm mb-3">
                  Replace system quantities with counted quantities after review.
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Before trading update</li>
                  <li>• After trading update</li>
                  <li>• Options for negatives and uncounted items</li>
                </ul>
              </div>
            </div>
          </button>

          {/* Stock Item Adjustment */}
          <button
            onClick={() => setCurrentOption('adjustments')}
            className="p-6 bg-white border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition text-left"
          >
            <div className="flex items-start gap-4">
              <Wrench className="text-gray-600" size={32} />
              <div>
                <h3 className="text-xl font-semibold mb-2">G. Stock Item Adjustment</h3>
                <p className="text-gray-600 text-sm mb-3">
                  Make manual adjustments to individual stock items without stock take.
                </p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Adjust single items</li>
                  <li>• Update without stock count</li>
                  <li>• Password protected</li>
                </ul>
              </div>
            </div>
          </button>
        </div>
      )}

      {currentOption === 'print-forms' && (
        <PrintStockTakeForms onBack={() => setCurrentOption('menu')} />
      )}

      {currentOption === 'count' && (
        <StockCount onBack={() => setCurrentOption('menu')} />
      )}

      {currentOption === 'variance' && (
        <VarianceReport onBack={() => setCurrentOption('menu')} />
      )}

      {currentOption === 'valuation' && (
        <StockValuation onBack={() => setCurrentOption('menu')} />
      )}

      {currentOption === 'update' && (
        <StockTakeUpdate onBack={() => setCurrentOption('menu')} />
      )}

      {currentOption === 'adjustments' && (
        <StockAdjustments onBack={() => setCurrentOption('menu')} />
      )}
    </div>
  );
}

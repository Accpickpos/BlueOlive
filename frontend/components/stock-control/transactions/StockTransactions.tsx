'use client';

import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import IncomingStock from './IncomingStock';
import StockReturns from './StockReturns';
import StockTakeMenu from './StockTakeMenu';
import ManufactureItems from './ManufactureItems';

interface StockTransactionsProps {
  onBack: () => void;
}

type MenuOption = 'main' | 'incoming' | 'returns' | 'stock-take' | 'manufacture';

export default function StockTransactions({ onBack }: StockTransactionsProps) {
  const [currentMenu, setCurrentMenu] = useState<MenuOption>('main');

  const handleBack = () => {
    if (currentMenu === 'main') {
      onBack();
    } else {
      setCurrentMenu('main');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition"
        >
          <ArrowLeft size={20} />
          Back
        </button>
        <h1 className="text-3xl font-bold">Stock Control - Transactions</h1>
        <div className="w-20" />
      </div>

      {currentMenu === 'main' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Incoming Stock */}
          <button
            onClick={() => setCurrentMenu('incoming')}
            className="p-6 bg-white border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition text-left"
          >
            <h3 className="text-xl font-semibold mb-2">Incoming Stock</h3>
            <p className="text-gray-600 text-sm mb-4">
              Updates Stock only. Use Creditors Transaction for Creditors updates.
            </p>
            <div className="text-xs text-gray-500">
              <p>• Enter invoice date</p>
              <p>• Select VAT option (Inclusive/Exclusive)</p>
              <p>• Add stock items and quantities</p>
            </div>
          </button>

          {/* Stock Returns */}
          <button
            onClick={() => setCurrentMenu('returns')}
            className="p-6 bg-white border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition text-left"
          >
            <h3 className="text-xl font-semibold mb-2">Stock Returns</h3>
            <p className="text-gray-600 text-sm mb-4">
              Process supplier returns to update stock quantities.
            </p>
            <div className="text-xs text-gray-500">
              <p>• Enter document date</p>
              <p>• Select VAT option</p>
              <p>• Add returned items</p>
            </div>
          </button>

          {/* Stock Take */}
          <button
            onClick={() => setCurrentMenu('stock-take')}
            className="p-6 bg-white border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition text-left"
          >
            <h3 className="text-xl font-semibold mb-2">Stock Take</h3>
            <p className="text-gray-600 text-sm mb-4">
              Print forms, count stock, review variance and update stock levels.
            </p>
            <div className="text-xs text-gray-500">
              <p>• Print stock take forms</p>
              <p>• Perform stock count</p>
              <p>• Review variance report</p>
            </div>
          </button>

          {/* Manufacture Items */}
          <button
            onClick={() => setCurrentMenu('manufacture')}
            className="p-6 bg-white border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition text-left"
          >
            <h3 className="text-xl font-semibold mb-2">Manufacture Item(s)</h3>
            <p className="text-gray-600 text-sm mb-4">
              Update stock of manufactured goods (bundles) and deplete ingredients.
            </p>
            <div className="text-xs text-gray-500">
              <p>• Select pack/bundle</p>
              <p>• Enter quantity manufactured</p>
              <p>• Confirm date of manufacture</p>
            </div>
          </button>
        </div>
      )}

      {currentMenu === 'incoming' && (
        <IncomingStock onBack={() => setCurrentMenu('main')} />
      )}

      {currentMenu === 'returns' && (
        <StockReturns onBack={() => setCurrentMenu('main')} />
      )}

      {currentMenu === 'stock-take' && (
        <StockTakeMenu onBack={() => setCurrentMenu('main')} />
      )}

      {currentMenu === 'manufacture' && (
        <ManufactureItems onBack={() => setCurrentMenu('main')} />
      )}
    </div>
  );
}

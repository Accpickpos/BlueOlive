'use client';

import { useState } from 'react';
import { useAuthContext, Shop } from '@/lib/AuthContext';

interface ShopSelectorProps {
  onShopChange?: (shop: Shop) => void;
}

export default function ShopSelector({ onShopChange }: ShopSelectorProps) {
  const { currentShop, accessibleShops, switchShop, isLoading, isAdmin } = useAuthContext();
  const [isOpen, setIsOpen] = useState(false);
  const [isSwitching, setIsSwitching] = useState(false);

  // Show current shop always - for visibility
  // Only hide entirely if there are no shops at all
  if (!accessibleShops || accessibleShops.length === 0) {
    return null;
  }

  // For this implementation: always show button and allow opening dropdown
  // The dropdown will show all shops the user has access to

  const handleSwitch = async (shop: Shop) => {
    if (shop.id === currentShop?.id) {
      setIsOpen(false);
      return;
    }

    setIsSwitching(true);
    try {
      await switchShop(shop.id);
      // After successful shop switch, reload the page to fetch fresh data
      window.location.reload();
    } catch (error) {
      console.error('Failed to switch shop:', error);
    } finally {
      setIsSwitching(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading || isSwitching}
        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
      >
        <svg
          className="w-4 h-4 text-gray-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
          />
        </svg>
        <span className="font-medium">
          {isSwitching ? 'Switching...' : currentShop?.name || 'No Shop Selected'}
        </span>
        {/* Always show dropdown arrow */}
        <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
      </button>

      {/* Always show dropdown menu when clicked */}
      {isOpen && accessibleShops.length > 0 && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
            <div className="p-2 border-b border-gray-100">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                Switch Shop
              </p>
            </div>
            <div className="p-1 max-h-64 overflow-y-auto">
              {accessibleShops.map((shop) => (
                <button
                  key={shop.id}
                  onClick={() => handleSwitch(shop)}
                  disabled={isSwitching}
                  className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left rounded-md transition-colors ${
                    shop.id === currentShop?.id
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  } disabled:opacity-50`}
                >
                  <div className="flex-1">
                    <p className="font-medium">{shop.name}</p>
                    {shop.is_head_office && (
                      <span className="text-xs text-indigo-600">Head Office</span>
                    )}
                  </div>
                  {shop.id === currentShop?.id && (
                    <svg
                      className="w-4 h-4 text-indigo-600"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

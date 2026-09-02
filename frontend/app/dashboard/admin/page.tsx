'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import ShopsListPanel from '@/components/ShopsListPanel';
import UsersListPanel from '@/components/UsersListPanel';
import OwnerRoute from '@/components/OwnerRoute';

function AdminPageContent() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [statusMessage, setStatusMessage] = useState<{type: 'success' | 'info', message: string} | null>(null);
  const searchParams = useSearchParams();
  
  useEffect(() => {
    const shopCreated = searchParams.get('shopCreated');
    const shopName = searchParams.get('shopName');
    const shopCreating = searchParams.get('shopCreating');
    
    if (shopCreated) {
      setStatusMessage({
        type: 'success',
        message: `Shop "${shopName || shopCreated}" has been created successfully! Setup is completing in the background.`
      });
    } else if (shopCreating) {
      setStatusMessage({
        type: 'info',
        message: `Creating shop "${shopName || ''}" - this may take a few minutes. The setup is running in the background.`
      });
    }
  }, [searchParams]);

  const handleSuccess = () => {
    // Trigger a refresh of both lists
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <OwnerRoute>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>

        {/* Status Messages */}
        {statusMessage && (
          <div className={`p-4 rounded-lg ${
            statusMessage.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-blue-50 text-blue-800 border border-blue-200'
          }`}>
            <div className="flex items-center justify-between">
              <span>{statusMessage.message}</span>
              <button
                onClick={() => setStatusMessage(null)}
                className="text-current opacity-60 hover:opacity-100"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Shops List */}
        <ShopsListPanel refreshKey={refreshKey} />

        {/* Users List */}
        <UsersListPanel refreshKey={refreshKey} />
      </div>
    </OwnerRoute>
  );
}

export default function AdminPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AdminPageContent />
    </Suspense>
  );
}

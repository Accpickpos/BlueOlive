'use client';

import { useState } from 'react';
import ShopsListPanel from '@/components/ShopsListPanel';
import UsersListPanel from '@/components/UsersListPanel';

export default function AdminPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleSuccess = () => {
    // Trigger a refresh of both lists
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
      
      {/* Shops List */}
      <ShopsListPanel refreshKey={refreshKey} />

      {/* Users List */}
      <UsersListPanel refreshKey={refreshKey} />
    </div>
  );
}

'use client';

import AdminRoute from '@/components/AdminRoute';
import { ReactNode } from 'react';

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AdminRoute>
      {children}
    </AdminRoute>
  );
}

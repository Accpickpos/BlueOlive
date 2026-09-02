'use client';
import { usePlatformAuth } from '@/lib/PlatformAuthContext';
import { ReactNode } from 'react';
import { Shield } from 'lucide-react';

interface PlatformOwnerRouteProps {
  children: ReactNode;
}

/**
 * Guards /owner/* pages. Checks the platform-owner session (is_superuser,
 * verified server-side by saas-admin/auth/profile/) - unrelated to
 * OwnerRoute/AdminRoute, which gate tenant-role access within /dashboard.
 */
export default function PlatformOwnerRoute({ children }: PlatformOwnerRouteProps) {
  const { owner, isLoading } = usePlatformAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-slate-400"></div>
      </div>
    );
  }

  if (!owner) {
    if (typeof window !== 'undefined' && !window.location.pathname.endsWith('/owner/login')) {
      window.location.href = '/owner/login';
    }
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900 text-slate-300 gap-2">
        <Shield className="h-5 w-5" />
        Redirecting to owner sign in...
      </div>
    );
  }

  return <>{children}</>;
}

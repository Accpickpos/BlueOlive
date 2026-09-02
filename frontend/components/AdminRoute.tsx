'use client';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/lib/AuthContext';
import { clearAuthData } from '@/lib/api';
import { ReactNode, useEffect, useState } from 'react';
import { AlertCircle, Home, Shield, LogOut } from 'lucide-react';
import Link from 'next/link';

interface AdminRouteProps {
  children: ReactNode;
}

/**
 * AdminRoute Component
 * Protects routes that require admin access
 * Shows access denied message for non-admin users (logged in as regular user)
 * Shows login required message for unauthenticated users
 *
 * Usage:
 * <AdminRoute>
 *   <AdminPanel />
 * </AdminRoute>
 */
export default function AdminRoute({ children }: AdminRouteProps) {
  const { user, isLoading, isAdmin, isAccountant } = useAuthContext();
  const hasAccess = isAdmin || isAccountant;
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);

  // Only render after mounting to avoid hydration mismatch
  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
          <div className="text-lg text-gray-600">Loading...</div>
        </div>
      </div>
    );
  }

  if (!isMounted || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
          <div className="text-lg text-gray-600">Loading...</div>
        </div>
      </div>
    );
  }

  // If we get here, we're mounted and auth check is complete
  console.log('AdminRoute check:', { user: user?.username, isAdmin, isAccountant, isLoading });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
          <div className="text-lg text-gray-600">Loading...</div>
        </div>
      </div>
    );
  }

  // User not authenticated - show login required message
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-purple-50 px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-lg shadow-xl p-8 border-t-4 border-indigo-600">
            <div className="flex justify-center mb-4">
              <div className="bg-indigo-50 rounded-full p-4">
                <Shield className="h-12 w-12 text-indigo-600" />
              </div>
            </div>
            
            <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">Admin Access Required</h1>
            
            <p className="text-gray-600 mb-6 text-center">
              This page is restricted to administrators and accountants. You need to log in with an admin or accountant account to access this area.
            </p>

            <div className="space-y-3 mb-6">
              <Link
                href="/auth"
                className="inline-block w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-3 px-4 rounded-lg transition flex items-center justify-center gap-2"
              >
                <Shield className="h-5 w-5" />
                Login as Admin
              </Link>
              
              <Link
                href="/dashboard"
                className="inline-block w-full bg-gray-100 hover:bg-gray-200 text-gray-900 font-medium py-2 px-4 rounded-lg transition flex items-center justify-center gap-2"
              >
                <Home className="h-5 w-5" />
                Back to Dashboard
              </Link>
            </div>

            <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
              <p className="text-sm text-amber-700">
                <strong>💡 Tip:</strong> If you're an administrator, make sure you're logged in with an admin account.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // User authenticated but lacks admin/accountant access - show access denied message
  if (!hasAccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-lg shadow-xl p-8 border-t-4 border-red-600">
            <div className="flex justify-center mb-4">
              <div className="bg-red-50 rounded-full p-4">
                <AlertCircle className="h-12 w-12 text-red-600" />
              </div>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">Access Denied</h1>

            <p className="text-gray-600 mb-2 text-center">
              You need to <strong>login as an admin or accountant</strong> to access this page.
            </p>

            <p className="text-sm text-gray-500 mb-6 text-center">
              Currently logged in as: <span className="font-semibold text-gray-700">{user?.username}</span> ({user?.role || 'User'})
            </p>

            <div className="space-y-3 mb-6">
              <button
                onClick={() => {
                  // Clear auth and redirect to login
                  clearAuthData();
                  router.push('/auth');
                }}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-3 px-4 rounded-lg transition flex items-center justify-center gap-2"
              >
                <LogOut className="h-5 w-5" />
                Login as Different User (Admin)
              </button>
              
              <Link
                href="/dashboard"
                className="inline-block w-full bg-gray-100 hover:bg-gray-200 text-gray-900 font-medium py-2 px-4 rounded-lg transition flex items-center justify-center gap-2"
              >
                <Home className="h-5 w-5" />
                Back to Dashboard
              </Link>
            </div>

            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-700">
                <strong>ℹ️ Note:</strong> This is an admin-only area. Regular users cannot access these features. Contact your administrator if you need admin access.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

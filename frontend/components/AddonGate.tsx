'use client';
import { ReactNode } from 'react';
import Link from 'next/link';
import { Home, PackageX } from 'lucide-react';
import { useAuthContext } from '@/lib/AuthContext';

/**
 * Blocks a route subtree for tenants that haven't enabled the given addon
 * (Tenant.enabled_addons - see settings.OPTIONAL_ADDON_APPS on the backend).
 *
 * Deliberately separate from AdminRoute: gas (checkout) is used by cashiers,
 * not just admins, so it needs an addon check without the admin/accountant
 * role check AdminRoute also does. cash_book/general_ledger/stockfinder
 * pages sit under /dashboard/admin, which AdminRoute already role-gates at
 * the layout above this one - this only adds the addon check on top.
 *
 * This is a UI-layer convenience (avoids rendering a page that will just
 * 404/403 against the backend). The real enforcement is
 * tenancy.middleware.AddonAccessMiddleware.
 */
export default function AddonGate({ addon, children }: { addon: string; children: ReactNode }) {
  const { hasAddon, isLoading } = useAuthContext();

  if (isLoading) {
    return null;
  }

  if (!hasAddon(addon)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-lg shadow-xl p-8 border-t-4 border-gray-400">
            <div className="flex justify-center mb-4">
              <div className="bg-gray-100 rounded-full p-4">
                <PackageX className="h-12 w-12 text-gray-500" />
              </div>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">Not Available</h1>

            <p className="text-gray-600 mb-6 text-center">
              This feature isn't enabled for your account. Contact your administrator if you'd like to add it.
            </p>

            <Link
              href="/dashboard"
              className="inline-block w-full bg-gray-100 hover:bg-gray-200 text-gray-900 font-medium py-2 px-4 rounded-lg transition flex items-center justify-center gap-2"
            >
              <Home className="h-5 w-5" />
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

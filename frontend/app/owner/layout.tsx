'use client';
import { PlatformAuthProvider } from '@/lib/PlatformAuthContext';
import { ReactNode } from 'react';

/**
 * Root layout for the platform-owner area. Deliberately does not reuse
 * frontend/app/dashboard/'s layout, nav, or AuthContext - this section is
 * for the SaaS platform owner (real Django superuser), not tenant staff,
 * and has no link pointing to it from anywhere in the tenant dashboard.
 */
export default function OwnerLayout({ children }: { children: ReactNode }) {
  return (
    <PlatformAuthProvider>
      <div className="min-h-screen bg-slate-950 text-slate-100">{children}</div>
    </PlatformAuthProvider>
  );
}

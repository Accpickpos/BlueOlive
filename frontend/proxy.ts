import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Middleware to protect routes from unauthorized access
 * Admin routes are protected by AdminRoute component on client-side
 * Regular dashboard routes are protected here
 */
export async function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;
  
  // Skip middleware for admin routes - they use AdminRoute component for better UX
  const isAdminPath = path.startsWith('/dashboard/admin');
  if (isAdminPath) {
    return NextResponse.next();
  }
  
  // Protect dashboard routes (but not admin subroutes)
  const isDashboardPath = path.startsWith('/dashboard');
  
  if (isDashboardPath) {
    try {
      // Make a server-side request to check user profile
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/v1/users/auth/profile/`, {
        headers: {
          'Cookie': request.headers.get('cookie') || '',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        // User is not authenticated, redirect to login
        return NextResponse.redirect(new URL('/auth', request.url));
      }

      // User is authenticated, allow access
      return NextResponse.next();
    } catch (error) {
      console.error('Middleware auth check failed:', error);
      // On error, redirect to login for safety
      return NextResponse.redirect(new URL('/auth', request.url));
    }
  }

  return NextResponse.next();
}

/**
 * Configure which routes should be protected by middleware
 */
export const config = {
  matcher: ['/dashboard/:path*'],
};
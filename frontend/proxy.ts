import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Get the API base URL based on the environment
 * - In local development: use localhost:8000
 * - In Docker/production: use blueolive-backend:8000
 */
function getApiBaseUrl(request: NextRequest): string {
  // Check if we're running locally by checking the origin
  const origin = request.headers.get('origin') || '';
  const isLocalhost = origin.includes('localhost') || origin.includes('127.0.0.1');
  
  // Use environment variable if set, otherwise determine based on origin
  if (process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE;
  }
  
  // Default based on whether request is from localhost
  return isLocalhost ? 'http://localhost:8000' : 'http://blueolive-backend:8000';
}

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
      const apiBase = getApiBaseUrl(request);
      console.log('Middleware: Checking auth, using API:', apiBase);
      
      const response = await fetch(`${apiBase}/api/v1/users/auth/profile/`, {
        headers: {
          'Cookie': request.headers.get('cookie') || '',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        // User is not authenticated, redirect to login
        console.log('Middleware: Auth check failed with status:', response.status);
        return NextResponse.redirect(new URL('/auth', request.url));
      }

      // User is authenticated, allow access
      console.log('Middleware: Auth check passed');
      return NextResponse.next();
    } catch (error) {
      console.error('Middleware auth check failed:', error);
      // On error, allow the request through - the client-side ProtectedRoute will handle auth
      // This is better than blocking access when the backend is unreachable
      console.log('Middleware: Allowing request through due to error');
      return NextResponse.next();
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
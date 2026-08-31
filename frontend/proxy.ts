import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Per-request Content-Security-Policy, applied via a nonce that Next.js
 * automatically attaches to its own injected scripts once it sees this
 * exact pattern (nonce set on both the request header, so `headers()` in
 * Server Components can read it, and the response header).
 *
 * script-src is nonce-gated + 'strict-dynamic' — this is the directive
 * that actually matters: it's what stops an injected <script> (e.g. a
 * future XSS that isn't caught by output-escaping) from executing, since
 * an attacker can't guess a fresh per-request nonce.
 *
 * style-src keeps 'unsafe-inline': Radix UI (Dialog/Select/Popover/
 * Tooltip, used throughout this app) positions itself via inline
 * `style="..."` attributes through its floating-ui-based positioning, and
 * CSP has no nonce mechanism for inline style *attributes* (only <style>
 * elements) — blocking this would break dropdown/dialog/tooltip
 * positioning app-wide, not stop any script execution (inline styles
 * can't run JS).
 *
 * connect-src includes the configured API origin(s) so fetch/XHR to the
 * Django backend isn't blocked. Add more origins to CSP_EXTRA_CONNECT_SRC
 * (space-separated) if a deployment calls additional API hosts (e.g.
 * per-tenant subdomains) not covered by NEXT_PUBLIC_API_BASE.
 */
function buildCspHeader(request: NextRequest, apiOrigin: string): { nonce: string; header: string } {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');

  const extraConnectSrc = (process.env.CSP_EXTRA_CONNECT_SRC || '')
    .split(/\s+/)
    .filter(Boolean);
  const connectSrc = ["'self'", apiOrigin, ...extraConnectSrc].filter(Boolean).join(' ');

  const isProd = process.env.NODE_ENV === 'production';

  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic';
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: blob: https:;
    font-src 'self' data:;
    connect-src ${connectSrc};
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    ${isProd ? "upgrade-insecure-requests;" : ""}
  `;

  return { nonce, header: cspHeader.replace(/\s{2,}/g, ' ').trim() };
}

/**
 * Get the API base URL based on the environment
 * - In local development: use localhost:8000
 * - In Docker/production: use blueolive-backend:8000
 */
function getApiBaseUrl(request: NextRequest): string {
  // Use environment variable if explicitly set - this takes precedence
  if (process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE;
  }

  // Check if we're running locally by checking the host header
  // The host header is always present and more reliable than origin
  const host = request.headers.get('host') || '';
  const isLocalhost = host.includes('localhost') || host.includes('127.0.0.1');
  
  // Also check x-forwarded-host for proxied requests
  const xForwardedHost = request.headers.get('x-forwarded-host') || '';
  const isForwardedToLocalhost = xForwardedHost.includes('localhost') || xForwardedHost.includes('127.0.0.1');
  
  // Default based on whether request is from localhost
  const isLocalRequest = isLocalhost || isForwardedToLocalhost;
  return isLocalRequest ? 'http://localhost:8000' : 'http://blueolive-backend:8000';
}

/**
 * Middleware to protect routes from unauthorized access
 * Admin routes are protected by AdminRoute component on client-side
 * Regular dashboard routes are protected here
 */
export async function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;

  let apiOrigin = '';
  try {
    apiOrigin = new URL(getApiBaseUrl(request)).origin;
  } catch {
    // Malformed API base — fall back to 'self' only in the CSP rather than
    // failing the request over a header.
  }
  const { nonce, header: cspHeader } = buildCspHeader(request, apiOrigin);

  // Nonce goes on the *request* headers too so Server Components can read
  // it via headers() (needed if a future inline <script> ever needs it),
  // and so Next.js's own injected scripts pick it up automatically.
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-nonce', nonce);
  requestHeaders.set('Content-Security-Policy', cspHeader);

  const withCsp = (res: NextResponse) => {
    res.headers.set('Content-Security-Policy', cspHeader);
    // Belt-and-suspenders alongside frame-ancestors above — some older
    // browsers only honor X-Frame-Options.
    res.headers.set('X-Frame-Options', 'DENY');
    return res;
  };
  const next = () =>
    withCsp(NextResponse.next({ request: { headers: requestHeaders } }));

  // Skip middleware for admin routes - they use AdminRoute component for better UX
  const isAdminPath = path.startsWith('/dashboard/admin');
  if (isAdminPath) {
    return next();
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
        return withCsp(NextResponse.redirect(new URL('/auth', request.url)));
      }

      // User is authenticated, allow access
      console.log('Middleware: Auth check passed');
      return next();
    } catch (error) {
      console.error('Middleware auth check failed:', error);
      // Fail closed: redirect to login rather than letting an unverifiable
      // request through. A dashboard route guards financial POS data, so a
      // backend hiccup here should degrade to "please log in again", not to
      // open access.
      return withCsp(NextResponse.redirect(new URL('/auth', request.url)));
    }
  }

  return next();
}

/**
 * Which routes this runs on. The auth-check logic above still only applies
 * to /dashboard/:path*, but the CSP/X-Frame-Options headers are worth
 * applying to every page (login, signup, etc.), not just the dashboard —
 * excludes static assets and the Next.js image optimizer for the same
 * reason the original matcher excluded them from the auth check.
 */
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)'],
};
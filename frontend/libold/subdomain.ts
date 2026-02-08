/**
 * Subdomain utility functions for multi-tenant frontend
 */

/**
 * Extract subdomain from current URL
 * localhost -> null (local development)
 * shop1.blueolive.com -> "shop1"
 * blueolive.com -> null (main domain, no subdomain)
 */
export function getSubdomainFromUrl(): string | null {
  if (typeof window === 'undefined') return null;
  
  const hostname = window.location.hostname;
  
  // Skip localhost and IP addresses
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname.includes(':')) {
    return null;
  }
  
  // Split by dots
  const parts = hostname.split('.');
  
  // If only one part (localhost), return null
  if (parts.length === 1) {
    return null;
  }
  
  // If more than 2 parts, first part is subdomain
  // example.com = 2 parts, no subdomain
  // shop1.example.com = 3 parts, shop1 is subdomain
  if (parts.length > 2) {
    return parts[0];
  }
  
  return null;
}

/**
 * Get the base domain (for API calls)
 * Returns the domain without subdomain
 * shop1.blueolive.com -> blueolive.com
 * localhost -> localhost:8000 (API)
 */
export function getBaseDomain(): string {
  if (typeof window === 'undefined') return 'localhost:8000';
  
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  const port = window.location.port;
  
  // For localhost or development
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `${protocol}//${hostname}${port ? ':' + port : ''}`;
  }
  
  // For production subdomains
  const parts = hostname.split('.');
  if (parts.length > 2) {
    // Remove subdomain, keep rest
    const baseDomain = parts.slice(1).join('.');
    return `${protocol}//${baseDomain}${port ? ':' + port : ''}`;
  }
  
  // Main domain, return as is
  return `${protocol}//${hostname}${port ? ':' + port : ''}`;
}

/**
 * Build full API URL with subdomain
 * If subdomain exists, prefix it to the request
 */
export function getApiBaseUrl(subdomain?: string | null): string {
  const baseDomain = getBaseDomain();
  
  if (subdomain && typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const port = window.location.port;
    
    // Build URL with subdomain
    return `${protocol}//${subdomain}.${hostname}${port ? ':' + port : ''}`;
  }
  
  return baseDomain;
}

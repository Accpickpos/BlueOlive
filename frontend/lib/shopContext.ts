/**
 * Shop Context Utility
 * Manages shop selection and storage in localStorage
 * Used for X-Shop-ID header in API calls
 */

export interface Shop {
  id: number;
  name: string;
  slug: string;
  tenant_id: number;
  is_active: boolean;
}

/**
 * Get the current shop ID from localStorage
 */
export function getCurrentShopId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('currentShopId');
}

/**
 * Get the current shop object from localStorage
 */
export function getCurrentShop(): Shop | null {
  if (typeof window === 'undefined') return null;
  const shopStr = localStorage.getItem('currentShop');
  if (!shopStr) return null;
  try {
    return JSON.parse(shopStr);
  } catch {
    return null;
  }
}

/**
 * Set the current shop in localStorage
 */
export function setCurrentShop(shop: Shop): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('currentShopId', String(shop.id));
  localStorage.setItem('currentShop', JSON.stringify(shop));
}

/**
 * Clear the current shop from localStorage
 */
export function clearCurrentShop(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('currentShopId');
  localStorage.removeItem('currentShop');
}

/**
 * Get all shops for the current tenant from localStorage
 */
export function getShops(): Shop[] {
  if (typeof window === 'undefined') return [];
  const shopsStr = localStorage.getItem('shops');
  if (!shopsStr) return [];
  try {
    return JSON.parse(shopsStr);
  } catch {
    return [];
  }
}

/**
 * Set all shops for the current tenant in localStorage
 */
export function setShops(shops: Shop[]): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('shops', JSON.stringify(shops));
}

/**
 * Get the tenant slug from localStorage
 */
export function getTenant(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('tenant');
}

/**
 * Set the tenant slug in localStorage
 */
export function setTenant(tenant: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('tenant', tenant);
}

/**
 * Clear all shop context from localStorage (but keep tenant for re-auth)
 */
export function clearShopContext(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('currentShopId');
  localStorage.removeItem('currentShop');
  localStorage.removeItem('shops');
}

/**
 * Clear all auth-related context including tenant
 */
export function clearAllContext(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('currentShopId');
  localStorage.removeItem('currentShop');
  localStorage.removeItem('shops');
  localStorage.removeItem('tenant');
}

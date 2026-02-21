'use client';
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiRequest } from './api';

export interface Shop {
  id: number;
  name: string;
  schema_name: string;
  is_head_office: boolean;
  is_current: boolean;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_superuser: boolean;
  is_admin: boolean;
  tenant_id: number | null;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  refetch: () => Promise<void>;
  // Shop-related properties
  currentShop: Shop | null;
  accessibleShops: Shop[];
  switchShop: (shopId: number) => Promise<void>;
  refetchShops: () => Promise<void>;
  // Subscribe to shop changes - useful for auto-refreshing data
  onShopChange: (callback: (shop: Shop) => void) => () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasAttemptedInitialFetch, setHasAttemptedInitialFetch] = useState(false);
  const [currentShop, setCurrentShop] = useState<Shop | null>(null);
  const [accessibleShops, setAccessibleShops] = useState<Shop[]>([]);
  
  // Shop change callbacks for auto-refresh
  const [shopChangeCallbacks, setShopChangeCallbacks] = useState<Set<(shop: Shop) => void>>(new Set());
  
  // Register callback for shop changes
  const onShopChange = useCallback((callback: (shop: Shop) => void) => {
    setShopChangeCallbacks(prev => {
      const newSet = new Set(prev);
      newSet.add(callback);
      return newSet;
    });
    // Return unsubscribe function
    return () => {
      setShopChangeCallbacks(prev => {
        const newSet = new Set(prev);
        newSet.delete(callback);
        return newSet;
      });
    };
  }, []);
  
  // Notify all subscribers when shop changes
  const notifyShopChange = useCallback((shop: Shop) => {
    shopChangeCallbacks.forEach(callback => {
      try {
        callback(shop);
      } catch (e) {
        console.error('Error in shop change callback:', e);
      }
    });
  }, [shopChangeCallbacks]);

  const refetchShops = useCallback(async () => {
    try {
      const response = await apiRequest('/api/v1/tenants/my-shops/');
      const shops = response.data as Shop[];
      setAccessibleShops(shops || []);
      
      // Find current shop
      const current = shops?.find((s: Shop) => s.is_current);
      if (current) {
        setCurrentShop(current);
      } else if (shops && shops.length > 0) {
        setCurrentShop(shops[0]);
      } else {
        setCurrentShop(null);
      }
    } catch (error: any) {
      // Don't crash if shops endpoint fails - user might not have shop access yet
      console.error('Could not fetch accessible shops:', error?.response?.data || error);
      setAccessibleShops([]);
      setCurrentShop(null);
    }
  }, []);

  const switchShop = useCallback(async (shopId: number) => {
    try {
      const response = await apiRequest('/api/v1/tenants/switch-shop/', {
        method: 'POST',
        data: { shop_id: shopId },
      });
      
      // Refresh shops after switching
      await refetchShops();
      
      return response.data;
    } catch (error) {
      console.error('Failed to switch shop:', error);
      throw error;
    }
  }, [refetchShops]);

  // Effect to notify subscribers when currentShop changes (e.g., after shop switch)
  useEffect(() => {
    if (currentShop && hasAttemptedInitialFetch) {
      notifyShopChange(currentShop);
    }
  }, [currentShop, hasAttemptedInitialFetch, notifyShopChange]);

  const refetch = useCallback(async (isInitialLoad: boolean = false) => {
    try {
      setIsLoading(true);
      // Cookies are sent automatically with withCredentials: true
      // No need to check localStorage
      const response = await apiRequest('/api/v1/users/auth/profile/', {
        skipRateLimitRetry: isInitialLoad, // Don't retry on initial load, just accept the failure
      });
      setUser(response.data);
      
      // Also fetch shops on profile fetch
      await refetchShops();
    } catch (error: any) {
      // 401 is expected when user hasn't logged in - don't log as error
      if (error?.response?.status === 401) {
        setUser(null);
        setCurrentShop(null);
        setAccessibleShops([]);
      } else if (error?.response?.status === 429) {
        // Rate limited
        if (isInitialLoad) {
          // On initial load, just accept it as "not logged in" to avoid blocking login
          console.debug('Profile endpoint rate limited on initial load - skipping retry');
        } else {
          // On explicit refetch (e.g., after login), log the issue
          console.warn('Rate limited on auth profile fetch - likely due to stale tokens');
        }
        setUser(null);
      } else if (error?.message === 'Network Error' || !error?.response) {
        // Network error - backend might not be running
        console.warn('Network error connecting to API. Backend may not be running at:', process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000');
        setUser(null);
      } else {
        console.error('Failed to fetch user profile:', error);
        setUser(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, [refetchShops]);

  useEffect(() => {
    // Only fetch user once on initial mount
    if (!hasAttemptedInitialFetch) {
      setHasAttemptedInitialFetch(true);
      // Mark as initial load so we don't retry on 429
      refetch(true);
    }
  }, [hasAttemptedInitialFetch, refetch]);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    isAdmin: user?.is_admin || false,
    refetch,
    currentShop,
    accessibleShops,
    switchShop,
    refetchShops,
    onShopChange,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to use authentication context
 * Must be used within AuthProvider
 */
export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }
  return context;
}

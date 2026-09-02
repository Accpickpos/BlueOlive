'use client';
import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { fetchPlatformProfile, platformLogin, platformLogout, PlatformOwner } from './platformApi';

interface PlatformAuthContextType {
  owner: PlatformOwner | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const PlatformAuthContext = createContext<PlatformAuthContextType | undefined>(undefined);

/**
 * Auth context for the platform-owner area (/owner/*).
 * Entirely separate from AuthContext (tenant users) - a different session,
 * different cookies, different backend endpoints. See lib/platformApi.ts.
 */
export function PlatformAuthProvider({ children }: { children: ReactNode }) {
  const [owner, setOwner] = useState<PlatformOwner | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refetch = useCallback(async () => {
    try {
      const profile = await fetchPlatformProfile();
      setOwner(profile);
    } catch {
      setOwner(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const login = useCallback(async (username: string, password: string) => {
    const profile = await platformLogin(username, password);
    setOwner(profile);
  }, []);

  const logout = useCallback(async () => {
    try {
      await platformLogout();
    } finally {
      setOwner(null);
    }
  }, []);

  return (
    <PlatformAuthContext.Provider
      value={{ owner, isLoading, isAuthenticated: owner !== null, login, logout }}
    >
      {children}
    </PlatformAuthContext.Provider>
  );
}

export function usePlatformAuth() {
  const context = useContext(PlatformAuthContext);
  if (!context) {
    throw new Error('usePlatformAuth must be used within PlatformAuthProvider');
  }
  return context;
}

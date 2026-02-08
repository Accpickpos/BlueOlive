// lib/useSettings.ts
"use client";

import { useState, useEffect, useCallback } from 'react';
import { api } from './api';

export interface SettingsData {
  departments: any[];
  salesAreas: any[];
  incomeCategories: any[];
  expenseCategories: any[];
  taxCodes: any[];
  paymentMethods: any[];
  creditTerms: any[];
  systemConfig: any;
}

const initialState: SettingsData = {
  departments: [],
  salesAreas: [],
  incomeCategories: [],
  expenseCategories: [],
  taxCodes: [],
  paymentMethods: [],
  creditTerms: [],
  systemConfig: null,
};

let cachedSettings: SettingsData | null = null;

/**
 * Custom hook to fetch and cache all settings/reference data
 * Use this hook in any component that needs access to settings
 */
export function useSettings() {
  const [settings, setSettings] = useState<SettingsData>(initialState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = useCallback(async (forceRefresh = false) => {
    // Return cached data if available and not forcing refresh
    if (cachedSettings && !forceRefresh) {
      setSettings(cachedSettings);
      return cachedSettings;
    }

    setLoading(true);
    setError(null);

    try {
      const [
        deptRes,
        areasRes,
        incomeRes,
        expenseRes,
        taxRes,
        paymentRes,
        creditRes,
        systemRes,
      ] = await Promise.all([
        api.get('/api/settings/departments/'),
        api.get('/api/settings/sales-areas/'),
        api.get('/api/settings/income-categories/'),
        api.get('/api/settings/expense-categories/'),
        api.get('/api/settings/tax-codes/'),
        api.get('/api/settings/payment-methods/'),
        api.get('/api/settings/credit-terms/'),
        api.get('/api/settings/system-config/'),
      ]);

      const data: SettingsData = {
        departments: deptRes.data.results || deptRes.data,
        salesAreas: areasRes.data.results || areasRes.data,
        incomeCategories: incomeRes.data.results || incomeRes.data,
        expenseCategories: expenseRes.data.results || expenseRes.data,
        taxCodes: taxRes.data.results || taxRes.data,
        paymentMethods: paymentRes.data.results || paymentRes.data,
        creditTerms: creditRes.data.results || creditRes.data,
        systemConfig: systemRes.data.results?.[0] || systemRes.data,
      };

      cachedSettings = data;
      setSettings(data);
      return data;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch settings';
      setError(errorMsg);
      console.error('Failed to fetch settings:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  return {
    ...settings,
    loading,
    error,
    refreshSettings: (force?: boolean) => fetchSettings(force),
  };
}

/**
 * Helper function to get a specific setting type without the hook
 * Useful for one-off requests
 */
export async function getSettingType(type: keyof SettingsData) {
  try {
    const endpoints: Record<keyof SettingsData, string> = {
      departments: '/api/settings/departments/',
      salesAreas: '/api/settings/sales-areas/',
      incomeCategories: '/api/settings/income-categories/',
      expenseCategories: '/api/settings/expense-categories/',
      taxCodes: '/api/settings/tax-codes/',
      paymentMethods: '/api/settings/payment-methods/',
      creditTerms: '/api/settings/credit-terms/',
      systemConfig: '/api/settings/system-config/',
    };

    const response = await api.get(endpoints[type]);
    return response.data.results || response.data;
  } catch (error) {
    console.error(`Failed to fetch ${type}:`, error);
    return null;
  }
}

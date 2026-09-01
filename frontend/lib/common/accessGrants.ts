/**
 * Common — Access Grants (role x module x function_type permission matrix).
 * Base URL: /api/v1/common/access-grants/
 *
 * Foundation only — not yet consulted by any viewset's permission_classes.
 * See apps/common/permissions.py's HasModuleFunctionAccess docstring.
 */

'use client';

import { api } from '../api';
import { ENDPOINTS } from '../api-config';

export type Role = 'ADMIN' | 'MANAGER' | 'STAFF' | 'CASHIER';
export type Module =
  | 'pos'
  | 'debtors'
  | 'creditors'
  | 'cash_book'
  | 'general_ledger'
  | 'stock_control'
  | 'purchase_orders'
  | 'settings';
export type FunctionType = 'MAINTENANCE' | 'TRANSACTIONS' | 'ENQUIRY' | 'REPORT';

export interface AccessGrant {
  id: number;
  role: Role;
  module: Module;
  function_type: FunctionType;
  is_allowed: boolean;
  updated_at: string;
}

export const ROLES: Role[] = ['ADMIN', 'MANAGER', 'STAFF', 'CASHIER'];
export const MODULES: Module[] = [
  'pos',
  'debtors',
  'creditors',
  'cash_book',
  'general_ledger',
  'stock_control',
  'purchase_orders',
  'settings',
];
export const FUNCTION_TYPES: FunctionType[] = ['MAINTENANCE', 'TRANSACTIONS', 'ENQUIRY', 'REPORT'];

export const accessGrantsApi = {
  list: async () => {
    const { data } = await api.get<{ results: AccessGrant[] } | AccessGrant[]>(
      ENDPOINTS.COMMON.ACCESS_GRANTS,
      { params: { page_size: 200 } }
    );
    return Array.isArray(data) ? data : data.results;
  },

  bulkUpdate: async (
    grants: { role: Role; module: Module; function_type: FunctionType; is_allowed: boolean }[]
  ) => {
    const { data } = await api.post<{ updated: number; missing: unknown[] }>(
      ENDPOINTS.COMMON.ACCESS_GRANTS_BULK_UPDATE,
      { grants }
    );
    return data;
  },
};

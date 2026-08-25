/**
 * Gas API Client — LPG cylinder rental/deposit tracking.
 *
 * Base URL: /api/v1/gas/
 * Backend: apps/gas (checkout / returned actions on RentalTransactionViewSet)
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export type ReconciliationState =
  | 'REFUNDED'
  | 'WRITTEN_OFF'
  | 'DISPUTED'
  | 'BILLED_FOR_REPLACEMENT';

export interface RentalTransaction {
  id: number;
  debtor: number;
  debtor_name: string;
  stock_item: string;
  stock_item_description: string;
  quantity: string;
  deposit_amount: string;
  status: 'OPEN' | 'RETURNED';
  checkout_date: string;
  due_date: string;
  returned_date: string | null;
  reconciliation_state: ReconciliationState | null;
  is_overdue: boolean;
  is_reconciled: boolean;
  reconciled_at: string | null;
  gl_batchno_checkout: number | null;
  gl_batchno_return: number | null;
  notes: string;
  created_at: string;
}

export interface RentalCheckoutData {
  debtor: number;
  stock_item: string;
  quantity: number;
  deposit_amount: number;
  reference?: string;
}

export interface RentalReturnData {
  reconciliation_state: ReconciliationState;
  replacement_unit_price?: number;
  reference?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string | null;
  previous?: string | null;
  results: T[];
}

export const gasApi = {
  /** List rentals — pass { status: 'OPEN' } etc. as needed by the backend filter. */
  list: async (params?: Record<string, string | number | boolean>) => {
    const response = await api.get<PaginatedResponse<RentalTransaction>>(
      ENDPOINTS.GAS.BASE,
      { params }
    );
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get<RentalTransaction>(ENDPOINTS.GAS.DETAIL(id));
    return response.data;
  },

  /** Check a cylinder out to a customer against a held deposit. */
  checkout: async (data: RentalCheckoutData) => {
    const response = await api.post<RentalTransaction>(ENDPOINTS.GAS.CHECKOUT, data);
    return response.data;
  },

  /**
   * Reconcile a cylinder return. WRITTEN_OFF / DISPUTED require an
   * Accountant/Admin role on the backend — a 403 here should be shown to the
   * user as a permission message, not a generic error.
   */
  returnCylinder: async (id: number, data: RentalReturnData) => {
    const response = await api.post<RentalTransaction>(ENDPOINTS.GAS.RETURN(id), data);
    return response.data;
  },
};

export default gasApi;

/**
 * Purchase Orders API Client
 * 
 * Handles all purchase order management endpoints:
 * - Purchase orders
 * - Receipts
 * - Back orders
 * - Templates
 * - Reports
 * 
 * Base URL: /api/v1/purchase-orders/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';
import type { PurchaseOrder, BackOrder, PaginatedPOResponse } from './types/purchaseOrders';

export interface Receipt {
  id?: number;
  order_id: number;
  receipt_date: string;
  quantity_received: number;
  reference?: string;
  notes?: string;
  created_at?: string;
  [key: string]: any;
}

export interface POTemplate {
  id?: number;
  name: string;
  description?: string;
  supplier_id: number;
  template_items: any[];
  created_at?: string;
  [key: string]: any;
}

export interface POReport {
  id?: number;
  name: string;
  report_type: 'PENDING' | 'OVERDUE' | 'RECEIVED' | 'SUMMARY';
  generated_date: string;
  data: any;
  [key: string]: any;
}

export const purchaseOrdersApi = {
  // ============ ORDERS ============
  orders: {
    /**
     * List all purchase orders
     */
    list: async (filters?: any) => {
      const response = await api.get<PaginatedPOResponse<PurchaseOrder>>(
        ENDPOINTS.PURCHASE_ORDERS.ORDERS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single purchase order
     */
    get: async (id: number | string) => {
      const response = await api.get<PurchaseOrder>(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}${id}/`
      );
      return response.data;
    },

    /**
     * Create new purchase order
     */
    create: async (data: Partial<PurchaseOrder>) => {
      const response = await api.post<PurchaseOrder>(
        ENDPOINTS.PURCHASE_ORDERS.ORDERS,
        data
      );
      return response.data;
    },

    /**
     * Update purchase order
     */
    update: async (id: number | string, data: Partial<PurchaseOrder>) => {
      const response = await api.patch<PurchaseOrder>(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete purchase order
     */
    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.PURCHASE_ORDERS.ORDERS}${id}/`);
    },

    /**
     * Approve purchase order
     */
    approve: async (id: number | string) => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}${id}/approve/`
      );
      return response.data;
    },

    /**
     * Close purchase order
     */
    close: async (id: number | string) => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}${id}/close/`
      );
      return response.data;
    },

    /**
     * Cancel purchase order
     */
    cancel: async (id: number | string) => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}${id}/cancel_order/`
      );
      return response.data;
    },

    /**
     * Receive stock against a purchase order (creates a GRN and, optionally,
     * a back order for any short delivery). Matches the receive_stock action
     * on PurchaseOrderViewSet.
     */
    receiveStock: async (id: number | string, data: {
      receipt_date?: string;
      invoice_number: string;
      line_items: Array<{
        purchase_order_line_id: number;
        quantity_received: number;
        actual_unit_cost?: number;
      }>;
      update_supplier_account?: boolean;
      create_back_order?: boolean;
    }) => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}${id}/receive_stock/`,
        data
      );
      return response.data;
    },
  },

  // ============ RECEIPTS ============
  receipts: {
    /**
     * List all receipts
     */
    list: async (filters?: any) => {
      const response = await api.get<{ results: Receipt[] }>(
        ENDPOINTS.PURCHASE_ORDERS.RECEIPTS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single receipt
     */
    get: async (id: number | string) => {
      const response = await api.get<Receipt>(
        `${ENDPOINTS.PURCHASE_ORDERS.RECEIPTS}${id}/`
      );
      return response.data;
    },

    /**
     * Create new receipt for purchase order
     */
    create: async (data: Partial<Receipt>) => {
      const response = await api.post<Receipt>(
        ENDPOINTS.PURCHASE_ORDERS.RECEIPTS,
        data
      );
      return response.data;
    },

    /**
     * Update receipt
     */
    update: async (id: number | string, data: Partial<Receipt>) => {
      const response = await api.patch<Receipt>(
        `${ENDPOINTS.PURCHASE_ORDERS.RECEIPTS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete receipt
     */
    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.PURCHASE_ORDERS.RECEIPTS}${id}/`);
    },
  },

  // ============ BACK ORDERS ============
  backOrders: {
    /**
     * List all back orders
     */
    list: async (filters?: any) => {
      const response = await api.get<{ results: BackOrder[] }>(
        ENDPOINTS.PURCHASE_ORDERS.BACK_ORDERS,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single back order
     */
    get: async (id: number | string) => {
      const response = await api.get<BackOrder>(
        `${ENDPOINTS.PURCHASE_ORDERS.BACK_ORDERS}${id}/`
      );
      return response.data;
    },

    /**
     * Create new back order
     */
    create: async (data: Partial<BackOrder>) => {
      const response = await api.post<BackOrder>(
        ENDPOINTS.PURCHASE_ORDERS.BACK_ORDERS,
        data
      );
      return response.data;
    },

    /**
     * Update back order
     */
    update: async (id: number | string, data: Partial<BackOrder>) => {
      const response = await api.patch<BackOrder>(
        `${ENDPOINTS.PURCHASE_ORDERS.BACK_ORDERS}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Close back order
     */
    close: async (id: number | string) => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.BACK_ORDERS}${id}/close/`
      );
      return response.data;
    },
  },

  // ============ TEMPLATES ============
  templates: {
    /**
     * List all PO templates
     */
    list: async (filters?: any) => {
      const response = await api.get<{ results: POTemplate[] }>(
        ENDPOINTS.PURCHASE_ORDERS.TEMPLATES,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get single PO template
     */
    get: async (id: number | string) => {
      const response = await api.get<POTemplate>(
        `${ENDPOINTS.PURCHASE_ORDERS.TEMPLATES}${id}/`
      );
      return response.data;
    },

    /**
     * Create new PO template
     */
    create: async (data: Partial<POTemplate>) => {
      const response = await api.post<POTemplate>(
        ENDPOINTS.PURCHASE_ORDERS.TEMPLATES,
        data
      );
      return response.data;
    },

    /**
     * Update PO template
     */
    update: async (id: number | string, data: Partial<POTemplate>) => {
      const response = await api.patch<POTemplate>(
        `${ENDPOINTS.PURCHASE_ORDERS.TEMPLATES}${id}/`,
        data
      );
      return response.data;
    },

    /**
     * Delete PO template
     */
    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.PURCHASE_ORDERS.TEMPLATES}${id}/`);
    },

    /**
     * Create order from template
     */
    createOrderFromTemplate: async (templateId: number | string, data: any) => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.TEMPLATES}${templateId}/create_order/`,
        data
      );
      return response.data;
    },
  },

  // ============ REPORTS ============
  reports: {
    /**
     * Get pending orders report
     */
    getPendingOrders: async (filters?: any) => {
      const response = await api.get(
        `${ENDPOINTS.PURCHASE_ORDERS.REPORTS}pending/`,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get overdue orders report
     */
    getOverdueOrders: async (filters?: any) => {
      const response = await api.get(
        `${ENDPOINTS.PURCHASE_ORDERS.REPORTS}overdue/`,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get received orders report
     */
    getReceivedOrders: async (filters?: any) => {
      const response = await api.get(
        `${ENDPOINTS.PURCHASE_ORDERS.REPORTS}received/`,
        { params: filters }
      );
      return response.data;
    },

    /**
     * Get summary report
     */
    getSummary: async (filters?: any) => {
      const response = await api.get(
        `${ENDPOINTS.PURCHASE_ORDERS.REPORTS}summary/`,
        { params: filters }
      );
      return response.data;
    },
  },

  // ============ UTILITIES ============
  utilities: {
    /**
     * Recalculate all order totals and VAT
     */
    recalculateTotals: async () => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}recalculate_totals/`
      );
      return response.data;
    },

    /**
     * Validate all orders for data integrity
     */
    validateOrders: async () => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}validate/`
      );
      return response.data;
    },

    /**
     * Find orders stuck in pending status
     */
    findStuckOrders: async (days?: number) => {
      const response = await api.get(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}stuck/`,
        { params: { days: days || 30 } }
      );
      return response.data;
    },

    /**
     * Find orphan line items
     */
    findOrphanItems: async () => {
      const response = await api.get(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}orphan_items/`
      );
      return response.data;
    },

    /**
     * Bulk update order status
     */
    bulkUpdateStatus: async (orderIds: (number | string)[], newStatus: string) => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}bulk_update/`,
        { order_ids: orderIds, new_status: newStatus }
      );
      return response.data;
    },

    /**
     * Export all orders data
     */
    exportOrders: async (format: 'csv' | 'xlsx' = 'xlsx') => {
      const response = await api.get(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}export/`,
        { params: { format } }
      );
      return response.data;
    },

    /**
     * Reindex files and rebuild search indexes
     */
    indexFiles: async () => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}reindex/`
      );
      return response.data;
    },

    /**
     * Reset quantities for all line items
     */
    resetQuantities: async () => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}reset_quantities/`
      );
      return response.data;
    },
  },
};

export default purchaseOrdersApi;

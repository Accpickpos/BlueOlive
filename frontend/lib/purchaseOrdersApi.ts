/**
 * Purchase Orders API Client
 *
 * Mirrors backend/core/apps/purchase_orders/{urls,views}.py — only real
 * endpoints are exposed here (no invented approve/close/reindex/bulk-update
 * actions the backend never implements).
 *
 * Base URL: /api/v1/purchase-orders/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';
import type {
  BackOrder,
  DeliveryVarianceItem,
  PaginatedPOResponse,
  PreOrderReportItem,
  PurchaseOrder,
  PurchaseOrderReceipt,
  PurchaseOrderTemplate,
  StockOnOrderItem,
} from './types/purchaseOrders';

export const purchaseOrdersApi = {
  // ============ ORDERS ============
  orders: {
    list: async (filters?: any) => {
      const response = await api.get<PaginatedPOResponse<PurchaseOrder>>(
        ENDPOINTS.PURCHASE_ORDERS.ORDERS,
        { params: filters }
      );
      return response.data;
    },

    get: async (orderNumber: number | string) => {
      const response = await api.get<PurchaseOrder>(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}${orderNumber}/`
      );
      return response.data;
    },

    /**
     * Create new purchase order. Matches PurchaseOrderCreateSerializer:
     * either extract_all_items/extract_below_reorder, or manual line_items.
     */
    create: async (data: {
      supplier: number;
      order_date?: string;
      delivery_date: string;
      pricing_method?: 'COST' | 'RETAIL';
      notes?: string;
      extract_all_items?: boolean;
      extract_below_reorder?: boolean;
      department?: number;
      line_items?: Array<{
        stock_item: string;
        quantity_ordered: number;
        unit_cost?: number;
        tax_code?: number;
        comments?: string;
        expense_category?: number;
      }>;
    }) => {
      const response = await api.post<PurchaseOrder>(ENDPOINTS.PURCHASE_ORDERS.ORDERS, data);
      return response.data;
    },

    update: async (orderNumber: number | string, data: Partial<PurchaseOrder>) => {
      const response = await api.patch<PurchaseOrder>(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}${orderNumber}/`,
        data
      );
      return response.data;
    },

    /**
     * Cancel purchase order. Matches PurchaseOrderViewSet.cancel_order —
     * blocks cancelling a fully-received order and reverses on-order
     * quantities. `reason` is stored on PurchaseOrder.cancellation_reason.
     */
    cancel: async (orderNumber: number | string, reason?: string) => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}${orderNumber}/cancel_order/`,
        { reason: reason || '' }
      );
      return response.data;
    },

    /**
     * Receive stock against a purchase order (creates a GRN and, optionally,
     * a back order for any short delivery). Matches the receive_stock action
     * on PurchaseOrderViewSet.
     */
    receiveStock: async (orderNumber: number | string, data: {
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
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}${orderNumber}/receive_stock/`,
        data
      );
      return response.data;
    },

    /**
     * Outstanding (status O/P) orders. Supports overdue=true and a
     * delivery_date_from/delivery_date_to range (Enquiries > By Delivery Date).
     */
    outstanding: async (params?: {
      overdue?: boolean;
      delivery_date_from?: string;
      delivery_date_to?: string;
    }) => {
      const response = await api.get<PurchaseOrder[]>(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}outstanding/`,
        { params }
      );
      return response.data;
    },

    bySupplier: async (supplier: number | string, status?: string) => {
      const response = await api.get<PurchaseOrder[]>(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}by_supplier/`,
        { params: { supplier, status } }
      );
      return response.data;
    },

    deliveryVarianceReport: async (params?: { start_date?: string; end_date?: string }) => {
      const response = await api.get<DeliveryVarianceItem[]>(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}delivery_variance_report/`,
        { params }
      );
      return response.data;
    },
  },

  // ============ RECEIPTS ============
  receipts: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: PurchaseOrderReceipt[] }>(
        ENDPOINTS.PURCHASE_ORDERS.RECEIPTS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<PurchaseOrderReceipt>(
        `${ENDPOINTS.PURCHASE_ORDERS.RECEIPTS}${id}/`
      );
      return response.data;
    },
  },

  // ============ BACK ORDERS ============
  backOrders: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: BackOrder[] }>(
        ENDPOINTS.PURCHASE_ORDERS.BACK_ORDERS,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<BackOrder>(
        `${ENDPOINTS.PURCHASE_ORDERS.BACK_ORDERS}${id}/`
      );
      return response.data;
    },
  },

  // ============ TEMPLATES ============
  templates: {
    list: async (filters?: any) => {
      const response = await api.get<{ results: PurchaseOrderTemplate[] }>(
        ENDPOINTS.PURCHASE_ORDERS.TEMPLATES,
        { params: filters }
      );
      return response.data;
    },

    get: async (id: number | string) => {
      const response = await api.get<PurchaseOrderTemplate>(
        `${ENDPOINTS.PURCHASE_ORDERS.TEMPLATES}${id}/`
      );
      return response.data;
    },

    create: async (data: Partial<PurchaseOrderTemplate>) => {
      const response = await api.post<PurchaseOrderTemplate>(
        ENDPOINTS.PURCHASE_ORDERS.TEMPLATES,
        data
      );
      return response.data;
    },

    update: async (id: number | string, data: Partial<PurchaseOrderTemplate>) => {
      const response = await api.patch<PurchaseOrderTemplate>(
        `${ENDPOINTS.PURCHASE_ORDERS.TEMPLATES}${id}/`,
        data
      );
      return response.data;
    },

    delete: async (id: number | string) => {
      await api.delete(`${ENDPOINTS.PURCHASE_ORDERS.TEMPLATES}${id}/`);
    },

    createOrderFromTemplate: async (templateId: number | string, deliveryDate?: string) => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.TEMPLATES}${templateId}/create_order_from_template/`,
        { delivery_date: deliveryDate }
      );
      return response.data;
    },
  },

  // ============ REPORTS ============
  reports: {
    stockOnOrder: async (supplier?: number | string) => {
      const response = await api.get<StockOnOrderItem[]>(
        `${ENDPOINTS.PURCHASE_ORDERS.REPORTS}stock_on_order/`,
        { params: { supplier } }
      );
      return response.data;
    },

    preOrderReport: async (supplier?: number | string) => {
      const response = await api.get<PreOrderReportItem[]>(
        `${ENDPOINTS.PURCHASE_ORDERS.REPORTS}pre_order_report/`,
        { params: { supplier } }
      );
      return response.data;
    },
  },

  // ============ UTILITIES ============
  utilities: {
    /**
     * Recompute every StockItem.quantity_on_order from actual outstanding PO
     * lines. Matches resync_po_quantities management command / the
     * resync_on_order_quantities action (Admin only).
     */
    resyncOnOrderQuantities: async () => {
      const response = await api.post(
        `${ENDPOINTS.PURCHASE_ORDERS.ORDERS}resync_on_order_quantities/`
      );
      return response.data;
    },
  },
};

export default purchaseOrdersApi;

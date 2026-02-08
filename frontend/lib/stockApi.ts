/**
 * Stock Control API Client
 * 
 * Handles all communication with Django backend for:
 * - Stock item maintenance
 * - Stock transactions
 * - Stock takes and valuations
 * 
 * Base URL: /api/v1/stock-control/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export interface StockItem {
  stock_code: string;
  description: string;
  department: string | number;
  supplier?: string | number;
  supplier_code?: string;
  tax_code: string | number;
  reorder_quantity: number;
  cost_price: number;
  allow_negative_quantities: boolean;
  bin_number?: string;
  is_kvi_item?: boolean;
  pack_details?: string;
  markup_1?: number;
  markup_2?: number;
  markup_3?: number;
  selling_price_1?: number;
  selling_price_2?: number;
  selling_price_3?: number;
  weight?: number;
  maximum_discount_percent?: number;
  is_active?: boolean;
}

/**
 * Get all stock items
 * @returns Paginated list of stock items or empty array if endpoint doesn't exist
 */
export async function getStockItems(params?: Record<string, any>): Promise<any> {
  try {
    const response = await api.get(ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS, { params });
    return response.data;
  } catch (err: any) {
    // If endpoint doesn't exist (404), return empty array
    if (err.response?.status === 404) {
      console.warn('Stock items endpoint not found. This endpoint may not be implemented on the backend.');
      return { results: [] };
    }
    throw err;
  }
}

/**
 * Get a single stock item by code
 */
export async function getStockItem(code: string): Promise<StockItem> {
  const response = await api.get(`${ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS}${code}/`);
  return response.data;
}

/**
 * Create a new stock item
 */
export async function createStockItem(data: StockItem): Promise<StockItem> {
  const response = await api.post(ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS, data);
  return response.data;
}

/**
 * Update an existing stock item
 */
export async function updateStockItem(code: string, data: Partial<StockItem>): Promise<StockItem> {
  const response = await api.put(`${ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS}${code}/`, data);
  return response.data;
}

/**
 * Delete a stock item
 */
export async function deleteStockItem(code: string): Promise<void> {
  await api.delete(`${ENDPOINTS.STOCK_CONTROL.STOCK_ITEMS}${code}/`);
}

/**
 * Record a stock transaction
 */
export async function recordTransaction(data: any): Promise<any> {
  const response = await api.post(ENDPOINTS.STOCK_CONTROL.TRANSACTIONS, data);
  return response.data;
}

/**
 * Get stock transactions
 */
export async function getTransactions(params?: Record<string, any>): Promise<any> {
  const response = await api.get(ENDPOINTS.STOCK_CONTROL.TRANSACTIONS, { params });
  return response.data;
}

/**
 * Get stock takes
 */
export async function getStockTakes(): Promise<any[]> {
  const response = await api.get('/api/stock-control/stock-takes/');
  return response.data.results || response.data || [];
}

/**
 * Create a new stock take
 */
export async function createStockTake(data: Record<string, any>): Promise<any> {
  const response = await api.post('/api/stock-control/stock-takes/', data);
  return response.data;
}

/**
 * Get items for a specific stock take
 */
export async function getStockTakeItems(stockTakeId: number | string): Promise<any[]> {
  const response = await api.get(`/api/stock-control/stock-takes/${stockTakeId}/items/`);
  return response.data.results || response.data || [];
}

/**
 * Add items to a stock take
 */
export async function addStockTakeItems(stockTakeId: number | string, items: Record<string, any>[]): Promise<any> {
  const response = await api.post(`/api/stock-control/stock-takes/${stockTakeId}/items/`, items);
  return response.data;
}

/**
 * Get special deals
 */
export async function getSpecialDeals(): Promise<any[]> {
  const response = await api.get('/api/stock-control/special-deals/');
  return response.data.results || response.data || [];
}

/**
 * Create a special deal
 */
export async function createSpecialDeal(data: Record<string, any>): Promise<any> {
  const response = await api.post('/api/stock-control/special-deals/', data);
  return response.data;
}

/**
 * Update a special deal
 */
export async function updateSpecialDeal(id: number, data: Record<string, any>): Promise<any> {
  const response = await api.put(`/api/stock-control/special-deals/${id}/`, data);
  return response.data;
}

/**
 * Delete a special deal
 */
export async function deleteSpecialDeal(id: number): Promise<void> {
  await api.delete(`/api/stock-control/special-deals/${id}/`);
}

/**
 * Get pack bundles for manufacture
 */
export async function getPackBundles(): Promise<any[]> {
  const response = await api.get('/api/stock-control/pack-bundles/');
  return response.data.results || response.data || [];
}

/**
 * Get stock summary (total items, stock value, low stock counts, etc.)
 */
export async function getStockSummary(): Promise<any> {
  const response = await api.get('/api/stock-control/summary/');
  return response.data;
}

/**
 * Get all departments
 */
export async function getDepartments(): Promise<any[]> {
  const response = await api.get('/api/stock-control/departments/');
  return response.data.results || response.data || [];
}

/**
 * Get all suppliers
 */
export async function getSuppliers(): Promise<any[]> {
  const response = await api.get('/api/stock-control/suppliers/');
  return response.data.results || response.data || [];
}

/**
 * Get special deals with filtering
 */
export async function getSpecialDealsFiltered(params?: Record<string, any>): Promise<any> {
  const response = await api.get('/api/stock-control/special-deals/', { params });
  return response.data;
}

/**
 * Get stock valuation
 */
export async function getStockValuation(params?: Record<string, any>): Promise<any> {
  const response = await api.get('/api/stock-control/valuation/', { params });
  return response.data;
}

/**
 * Get stock movements/transactions
 */
export async function getStockMovements(params?: Record<string, any>): Promise<any[]> {
  const response = await api.get('/api/stock-control/movements/', { params });
  return response.data.results || response.data || [];
}

/**
 * Get stock take list with filtering
 */
export async function getStockTakeList(params?: Record<string, any>): Promise<any> {
  const response = await api.get('/api/stock-control/stock-takes/', { params });
  return response.data;
}

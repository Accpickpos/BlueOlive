/**
 * Stock API
 * 
 * This module provides a convenient way to import stock control functions.
 * It re-exports from stockControlApi for backward compatibility.
 * 
 * For the full stock control API object, import from stockControlApi instead:
 * import { stockControlApi } from '@/lib/stockControlApi';
 */

export {
  getStockItem,
  getStockItems,
  createStockItem,
  updateStockItem,
  deleteStockItem,
  getStockItemPricing,
  getStockItemTransactions,
  adjustStockItem,
  getTransactions,
  recordTransaction,
  getStockSummary,
} from './stockControlApi';

// Also re-export the stockControlApi object for advanced usage
export { stockControlApi } from './stockControlApi';
export { stockControlApi as stockApi } from './stockControlApi';

/**
 * Components Index
 * 
 * Master barrel export for all components.
 * Import components from here instead of deep paths:
 * 
 *   import { Button, Card } from '@/components/ui';
 *   import { CreditorsMaintenance } from '@/components/creditors';
 *   import { DebtorsList } from '@/components/debtors';
 * 
 * Or import specific components directly from feature modules:
 * 
 *   import { StockItemMaintenance } from '@/components/stock-control';
 *   import { PurchaseOrderWizard } from '@/components/purchase-orders';
 */

// UI Primitives
export * from './ui';

// Layout Components (navbar, sidebar, error boundary)
export * from './layout';

// Auth Components (route guards)
export * from './auth';

// Modal Components
export * from './modals';

// Feature Components
export * from './cash-book';
export * from './creditors';
export * from './debtors';
export * from './import';
export * from './pos';
export * from './purchase-orders';
export * from './stock-control';

// Re-export root-level components that don't fit in other categories
export { default as DebtorsList } from './DebtorsList';
export { default as ShopSelector } from './ShopSelector';
export { default as ShopsListPanel } from './ShopsListPanel';
export { default as UsersListPanel } from './UsersListPanel';

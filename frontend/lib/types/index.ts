/**
 * Types Index
 * 
 * Due to type conflicts between modules, prefer importing types directly:
 * import { Creditor } from '@/lib/types/creditors';
 * import { Debtor } from '@/lib/types/debtors';
 * 
 * This barrel export provides types that don't conflict.
 */

// Non-conflicting type exports
export * from './stockControl';

# Invoice Consolidation Summary

## Objective
Consolidate invoice models by eliminating duplicate Invoice and InvoiceLine models from the `debtors` app and ensuring POS creates DebtorTransaction records instead, routing all invoices through the `pos.Invoice` model.

## Changes Made

### 1. Model Layer Changes

#### Removed from `backend/core/apps/debtors/models.py`
- **Invoice** model - Duplicate of pos.Invoice with state machine workflow
- **InvoiceLine** model - Associated line items for debtors invoices

**Rationale**: POS already has comprehensive Invoice and InvoiceLine models with full state machine support. Maintaining two Invoice implementations creates:
- Data duplication risk
- Inconsistent transaction tracking
- Maintenance complexity
- API endpoint confusion

#### Updated
- Fixed import error: Changed `MaxValidator` to `MaxValueValidator` (line 6 and 788) to resolve Django validator compatibility

### 2. API Layer Changes

#### Removed from `backend/core/apps/debtors/views.py`
- **InvoiceViewSet** - Full CRUD operations and custom actions
  - Removed: post_invoice, mark_as_paid, cancel, by_debtor, by_date_range actions
- Updated imports to source Invoice model from pos app instead

#### Updated Imports
- Refactored to import Invoice from `apps.pos.models` for DocumentSearchViewSet

### 3. Serializers

#### Removed from `backend/core/apps/debtors/serializers.py`
- InvoiceLineSerializer
- InvoiceListSerializer
- InvoiceDetailSerializer
- InvoiceCreateUpdateSerializer

#### Added to `backend/core/apps/pos/serializers.py`
- InvoiceLineSerializer (enhanced from pos perspective)
- InvoiceListSerializer (with sale area details)
- InvoiceDetailSerializer (with full state tracking)
- InvoiceCreateUpdateSerializer (with transaction handling)

These serializers are now consolidated in the POS app where the authoritative Invoice model exists.

### 4. Filters

#### Removed from `backend/core/apps/debtors/filters.py`
- **InvoiceFilter** - Filter for debtors Invoice model
- Updated imports to remove Invoice reference

### 5. URL Routing

#### Updated `backend/core/apps/debtors/urls.py`
- Removed router registration: `router.register(r'invoices', views.InvoiceViewSet, basename='invoice')`
- Invoice endpoints now available through the POS API

#### POS API Endpoints
Invoice management is now exclusively available through:
- `/api/pos/invoices/` - List and CRUD operations
- `/api/pos/invoices/{id}/post/` - Post invoice
- `/api/pos/invoices/{id}/mark-as-paid/` - Mark as paid
- `/api/pos/invoices/{id}/cancel/` - Cancel invoice

### 6. Services Layer

#### Updated `backend/core/apps/pos/services.py`
- Consolidated imports: Invoice and InvoiceLine now sourced directly from pos.models
- Ensures all invoice operations use the unified pos.Invoice model
- All service methods continue to create DebtorTransaction records when invoices are posted

### 7. Cross-App Integration

#### Updated `backend/core/apps/pos/views.py`
- Fixed InvoiceDetailSerializer import to source from pos.serializers instead of debtors.serializers
- Maintains backward compatibility for invoice operations

### 8. Database Migrations

#### Created `backend/core/apps/debtors/migrations/0010_remove_invoice_consolidation.py`
- Migration to delete Invoice and InvoiceLine models from debtors app
- Removes duplicate database tables
- Safe deletion with proper dependency handling

## Benefits

1. **Single Source of Truth**: One unified Invoice model across the entire system
2. **Consistency**: All invoices tracked through DebtorTransaction when posted
3. **Reduced Complexity**: Simplified API surface and fewer duplicate implementations
4. **Maintenance**: Single location to modify invoice logic
5. **Performance**: No more cross-app confusion or duplicate data
6. **Transaction Integrity**: DebtorTransaction remains the authoritative ledger

## Data Flow

```
POS Invoice Creation
    ↓
pos.Invoice Model (CRUD via /api/pos/invoices/)
    ↓
Invoice Posted
    ↓
DebtorTransaction Created (for accounts integration)
    ↓
Debtor Account Updated
```

## Migration Path

1. Existing debtors Invoice data should be migrated to pos.Invoice before applying the removal migration
2. All outstanding invoices must be transferred preserving:
   - Debtor relationships
   - Line items and totals
   - Payment status
   - Transaction dates

## Testing Checklist

- [ ] POS invoice creation still works
- [ ] Invoice posting creates DebtorTransaction records
- [ ] Payment tracking functions normally
- [ ] Debtor account balance calculations remain accurate
- [ ] DocumentSearchViewSet searches invoices correctly
- [ ] API endpoints respond with correct status codes
- [ ] Old debtors Invoice API endpoints return 404
- [ ] Invoice serializers from pos app work correctly

## Future Considerations

- Monitor pos.Invoice for any functionality requirements from debtors app
- Consider batch operations API for bulk invoice posting
- Implement webhook support for invoice status changes
- Add audit logging for invoice modifications

## Files Modified

1. `backend/core/apps/debtors/models.py`
2. `backend/core/apps/debtors/views.py`
3. `backend/core/apps/debtors/serializers.py`
4. `backend/core/apps/debtors/filters.py`
5. `backend/core/apps/debtors/urls.py`
6. `backend/core/apps/pos/models.py` (no changes, already complete)
7. `backend/core/apps/pos/serializers.py` (added invoice serializers)
8. `backend/core/apps/pos/services.py` (updated imports)
9. `backend/core/apps/pos/views.py` (fixed imports)
10. `backend/core/apps/debtors/migrations/0010_remove_invoice_consolidation.py` (new)

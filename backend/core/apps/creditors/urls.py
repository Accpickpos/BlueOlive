# backend/core/apps/creditors/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import (
    CreditorViewSet,
    GoodsReceivedNoteViewSet, GRNLineItemViewSet,
    CreditorInvoiceViewSet, CreditorInvoiceLineItemViewSet,
    CreditorCreditNoteViewSet, CreditorCreditNoteLineItemViewSet,
    CreditorPaymentViewSet,
    CreditorJournalViewSet,
    SupplierLedgerEntryViewSet,
    CreditorOpenItemViewSet, OpenItemAllocationViewSet,
    OpenItemAuditViewSet,
    RFCViewSet, RFCLineItemViewSet,
    ExpenseCategoryMonthlyBalanceViewSet,
    ExpenseCategoryTransactionViewSet,
    SupplierPaymentOrderViewSet,
    CreditorTransactionLineViewSet,
    OutstandingBalanceViewSet,
)

# ============================================================================
# ROOT ROUTER
# Registers all top-level viewsets.
# ============================================================================

router = DefaultRouter()

router.register(r'creditors',             CreditorViewSet,                      basename='creditor')
router.register(r'grns',                  GoodsReceivedNoteViewSet,             basename='grn')
router.register(r'invoices',              CreditorInvoiceViewSet,               basename='invoice')
router.register(r'credit_notes',          CreditorCreditNoteViewSet,            basename='credit-note')
router.register(r'payments',              CreditorPaymentViewSet,               basename='payment')
router.register(r'journals',              CreditorJournalViewSet,               basename='journal')
router.register(r'ledger',               SupplierLedgerEntryViewSet,           basename='ledger')
router.register(r'open_items',            CreditorOpenItemViewSet,              basename='open-item')
router.register(r'open_item_allocations', OpenItemAllocationViewSet,            basename='open-item-allocation')
router.register(r'open_item_audits',      OpenItemAuditViewSet,                 basename='open-item-audit')
router.register(r'rfcs',                  RFCViewSet,                           basename='rfc')
router.register(r'expense_monthly',       ExpenseCategoryMonthlyBalanceViewSet, basename='expense-monthly')
router.register(r'expense_transactions',  ExpenseCategoryTransactionViewSet,    basename='expense-transaction')
router.register(r'payment_orders',        SupplierPaymentOrderViewSet,          basename='payment-order')
router.register(r'transaction_lines',     CreditorTransactionLineViewSet,       basename='transaction-line')
router.register(r'outstanding-balances', OutstandingBalanceViewSet,             basename='outstanding-balance')

# ============================================================================
# NESTED ROUTERS
# Line items sit under their parent documents:
#   /grns/{grn_pk}/lines/
#   /invoices/{invoice_pk}/lines/
#   /credit_notes/{cn_pk}/lines/
#   /rfcs/{rfc_pk}/lines/
# ============================================================================

grn_router = nested_routers.NestedDefaultRouter(router, r'grns', lookup='grn')
grn_router.register(r'lines', GRNLineItemViewSet, basename='grn-line')

invoice_router = nested_routers.NestedDefaultRouter(router, r'invoices', lookup='invoice')
invoice_router.register(r'lines', CreditorInvoiceLineItemViewSet, basename='invoice-line')

cn_router = nested_routers.NestedDefaultRouter(router, r'credit_notes', lookup='cn')
cn_router.register(r'lines', CreditorCreditNoteLineItemViewSet, basename='credit-note-line')

rfc_router = nested_routers.NestedDefaultRouter(router, r'rfcs', lookup='rfc')
rfc_router.register(r'lines', RFCLineItemViewSet, basename='rfc-line')

# ============================================================================
# URL PATTERNS
# ============================================================================

urlpatterns = [
    path('', include(router.urls)),
    path('', include(grn_router.urls)),
    path('', include(invoice_router.urls)),
    path('', include(cn_router.urls)),
    path('', include(rfc_router.urls)),
]


# ============================================================================
# COMPLETE URL REFERENCE
# ============================================================================
#
# CREDITORS
#   GET    /creditors/                            list
#   POST   /creditors/                            create
#   GET    /creditors/{id}/                       detail
#   PUT    /creditors/{id}/                       update
#   PATCH  /creditors/{id}/                       partial update
#   DELETE /creditors/{id}/                       delete
#   GET    /creditors/{id}/aged_balances/         aging snapshot
#   POST   /creditors/{id}/recalculate_aged/      recalculate aging from open items
#   GET    /creditors/{id}/open_items/            outstanding open items for creditor
#   GET    /creditors/{id}/ledger/                full suptran ledger for creditor
#   GET    /creditors/{id}/transactions/          transaction type summary counts
#   GET    /creditors/age_analysis/               age analysis across all creditors
#
# GOODS RECEIVED NOTES
#   GET    /grns/                                 list
#   POST   /grns/                                 create (with nested line_items)
#   GET    /grns/{id}/                            detail
#   PUT    /grns/{id}/                            update header
#   PATCH  /grns/{id}/                            partial update header
#   DELETE /grns/{id}/                            delete (not posted only)
#   POST   /grns/{id}/post/                       mark as posted
#   GET    /grns/by_creditor/?creditor={id}       filter by creditor
#   GET    /grns/{grn_pk}/lines/                  list line items
#   POST   /grns/{grn_pk}/lines/                  add line item
#   GET    /grns/{grn_pk}/lines/{id}/             line item detail
#   PUT    /grns/{grn_pk}/lines/{id}/             update line item
#   DELETE /grns/{grn_pk}/lines/{id}/             delete line item
#
# CREDITOR INVOICES (expense)
#   GET    /invoices/                             list
#   POST   /invoices/                             create (with nested line_items)
#   GET    /invoices/{id}/                        detail
#   PUT    /invoices/{id}/                        update header
#   DELETE /invoices/{id}/                        delete (not posted only)
#   POST   /invoices/{id}/post/                   mark as posted
#   GET    /invoices/{invoice_pk}/lines/           list lines
#   POST   /invoices/{invoice_pk}/lines/           add line
#   GET    /invoices/{invoice_pk}/lines/{id}/      line detail
#   PUT    /invoices/{invoice_pk}/lines/{id}/      update line
#   DELETE /invoices/{invoice_pk}/lines/{id}/      delete line
#
# CREDIT NOTES
#   GET    /credit_notes/                         list
#   POST   /credit_notes/                         create (with nested line_items)
#   GET    /credit_notes/{id}/                    detail
#   PUT    /credit_notes/{id}/                    update header
#   DELETE /credit_notes/{id}/                    delete (not posted only)
#   POST   /credit_notes/{id}/post/               mark as posted
#   GET    /credit_notes/{cn_pk}/lines/           list lines
#   POST   /credit_notes/{cn_pk}/lines/           add line
#   PUT    /credit_notes/{cn_pk}/lines/{id}/      update line
#   DELETE /credit_notes/{cn_pk}/lines/{id}/      delete line
#
# PAYMENTS
#   GET    /payments/                             list
#   POST   /payments/                             create
#   GET    /payments/{id}/                        detail
#   PUT    /payments/{id}/                        update
#   DELETE /payments/{id}/                        delete (not posted only)
#   POST   /payments/{id}/post/                   mark as posted
#   POST   /payments/{id}/allocate/               allocate to open items
#
# JOURNALS
#   GET    /journals/                             list
#   POST   /journals/                             create
#   GET    /journals/{id}/                        detail
#   PUT    /journals/{id}/                        update
#   DELETE /journals/{id}/                        delete (not posted only)
#   POST   /journals/{id}/post/                   mark as posted
#
# SUPPLIER LEDGER (read-only)
#   GET    /ledger/                               list all suptran entries
#   GET    /ledger/{id}/                          single entry
#
# OPEN ITEMS
#   GET    /open_items/                           list
#   GET    /open_items/{id}/                      detail
#   PATCH  /open_items/{id}/                      partial update (is_legacy flag only)
#   GET    /open_items/outstanding/               unallocated items only
#   GET    /open_items/by_creditor/?creditor={id} filter by creditor
#
# OPEN ITEM ALLOCATIONS
#   GET    /open_item_allocations/                list
#   POST   /open_item_allocations/                create allocation
#   GET    /open_item_allocations/{id}/           detail
#   DELETE /open_item_allocations/{id}/           reverse allocation
#
# OPEN ITEM AUDITS (read-only)
#   GET    /open_item_audits/                     list
#   GET    /open_item_audits/{id}/                detail
#
# RFCs (RETURNS FOR CREDIT)
#   GET    /rfcs/                                 list
#   POST   /rfcs/                                 create (with nested line_items)
#   GET    /rfcs/{id}/                            detail
#   PUT    /rfcs/{id}/                            update
#   DELETE /rfcs/{id}/                            delete
#   GET    /rfcs/by_status/?status={PE|CR|RE|CA}  filter by status
#   PATCH  /rfcs/{id}/update_status/              change status
#   GET    /rfcs/{rfc_pk}/lines/                  list line items
#   POST   /rfcs/{rfc_pk}/lines/                  add line item
#   GET    /rfcs/{rfc_pk}/lines/{id}/             line detail
#   PUT    /rfcs/{rfc_pk}/lines/{id}/             update line
#   DELETE /rfcs/{rfc_pk}/lines/{id}/             delete line
#
# EXPENSE MONTHLY BALANCES (read-only)
#   GET    /expense_monthly/                      list
#   GET    /expense_monthly/{id}/                 detail
#   GET    /expense_monthly/?year={year}           filter by year
#   GET    /expense_monthly/?expense_category={id} filter by category
#
# EXPENSE TRANSACTIONS (read-only)
#   GET    /expense_transactions/                 list
#   GET    /expense_transactions/{id}/            detail
#   GET    /expense_transactions/by_creditor/?creditor={id}
#   GET    /expense_transactions/by_category/?category={id}
#
# SUPPLIER PAYMENT ORDERS
#   GET    /payment_orders/                       list
#   POST   /payment_orders/                       create
#   GET    /payment_orders/{id}/                  detail
#   PUT    /payment_orders/{id}/                  update
#   DELETE /payment_orders/{id}/                  delete
#   GET    /payment_orders/pending/               unprocessed orders
#   POST   /payment_orders/{id}/process/          mark as processed (payment run)
#
# TRANSACTION LINES (generic)
#   GET    /transaction_lines/                    list
#   POST   /transaction_lines/                    create
#   GET    /transaction_lines/{id}/               detail
#   PUT    /transaction_lines/{id}/               update
#   DELETE /transaction_lines/{id}/               delete
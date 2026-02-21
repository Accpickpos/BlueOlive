# DebtorTransaction Central Store Implementation

## Overview

DebtorTransaction has been enhanced to serve as the central transaction store for all debtor activities. This enables powerful querying, analysis, and reporting capabilities with a clean, intuitive API.

## New Features

### 1. Source Tracking

Track where transactions originate from to maintain audit trails and enable data reconciliation.

```python
# Transaction source choices
SOURCE_CHOICES = [
    ('POS', 'Point of Sale'),           # Direct POS terminal
    ('INVOICE', 'Invoice Entry'),       # Manual invoice creation
    ('IMPORT', 'Bulk Import'),          # Batch import from external systems
    ('MANUAL', 'Manual Entry'),         # System admin entry
]
```

**Fields:**
- `source_type` - CharField with source origin
- `source_reference` - CharField to link back to original record (invoice ID, batch ID, etc.)

**Example:**
```python
# Create transaction from POS
transaction = DebtorTransaction.objects.create(
    debtor=debtor,
    transaction_type='CS',
    transaction_date=date.today(),
    subtotal=1000.00,
    vat_amount=150.00,
    total_amount=1150.00,
    source_type='POS',
    source_reference='POS-TERMINAL-01-2024-02-13'
)

# Create transaction from bulk import
import_transaction = DebtorTransaction.objects.create(
    debtor=debtor,
    transaction_type='IN',
    transaction_date=date.today(),
    subtotal=5000.00,
    vat_amount=750.00,
    total_amount=5750.00,
    source_type='IMPORT',
    source_reference='BATCH-20240213-001'
)
```

### 2. Allocation Tracking

Track whether transactions have been fully allocated/paid against receipts.

```python
# Field
is_allocated = BooleanField(default=False, db_index=True)
```

**Usage:**
```python
# Find unpaid invoices
unpaid_invoices = DebtorTransaction.objects.filter(
    transaction_type='IN',
    is_allocated=False
)

# Mark transaction as paid
transaction.is_allocated = True
transaction.save()

# Get outstanding balance by debtor
outstanding = DebtorTransaction.objects.filter(
    is_allocated=False,
    transaction_type__in=['IN', 'CS']
).values('debtor__name').annotate(
    total_outstanding=Sum('total_amount')
)
```

### 3. Enhanced QuerySet with Business Logic Methods

Use custom QuerySet methods for common business operations:

```python
from apps.debtors.models import DebtorTransaction
from datetime import date, timedelta

# Get all invoices
DebtorTransaction.objects.invoices()

# Get all payments and receipts
DebtorTransaction.objects.payments()

# Get credit notes and refunds
DebtorTransaction.objects.credits()

# Get manual journal entries
DebtorTransaction.objects.journal_entries()

# Get interest charges
DebtorTransaction.objects.interest_charges()

# Get transactions in date range
DebtorTransaction.objects.by_period(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31)
)

# Get unallocated transactions
DebtorTransaction.objects.outstanding()

# Get allocated transactions
DebtorTransaction.objects.allocated()

# Get transactions by source
DebtorTransaction.objects.by_source('POS')

# Get transactions from bulk import
import_txns = DebtorTransaction.objects.by_source('IMPORT')
```

### 4. Aging Analysis Helper

Analyze outstanding transactions by age bucket:

```python
# Get aging summary as of today
aging = DebtorTransaction.objects.aging_analysis()
# Returns: {
#     'current': 15000.00,      # 0-30 days
#     'days_30_60': 8000.00,    # 30-60 days
#     'days_60_90': 5000.00,    # 60-90 days
#     'days_90_plus': 12000.00  # 90+ days
# }

# Get aging as of specific date
as_of_date = date(2024, 1, 31)
aging = DebtorTransaction.objects.aging_analysis(as_of_date=as_of_date)

# Manual aging calculation for specific debtor
aging = DebtorTransaction.objects.filter(
    debtor=debtor
).aging_analysis()
```

## Enhanced Filters

### DebtorTransactionFilter

Use these filters in API calls for powerful analysis:

```python
# Example API calls with filters
GET /api/debtors/transactions/?date_from=2024-01-01&date_to=2024-01-31
GET /api/debtors/transactions/?source_type=POS
GET /api/debtors/transactions/?is_allocated=false
GET /api/debtors/transactions/?age_bucket=90_plus
GET /api/debtors/transactions/?year=2024&month=2
GET /api/debtors/transactions/?quarter=1&transaction_type=IN
GET /api/debtors/transactions/?transaction_type=IN&is_allocated=false
```

**Available Filters:**
- `debtor` - Filter by specific debtor
- `transaction_type` - Filter by type (IN, CN, CS, CR, PM, RCP, INT, JD, JC, RF)
- `date_from` - Transactions on or after this date
- `date_to` - Transactions on or before this date
- `min_amount` - Minimum transaction amount
- `max_amount` - Maximum transaction amount
- `reference` - Search by transaction reference
- `source_type` - Filter by source (POS, INVOICE, IMPORT, MANUAL)
- `is_allocated` - Filter allocated/unallocated
- `status` - Filter by status (draft, posted, void, reversed)
- `has_balance` - Filter to unallocated transactions only
- `age_bucket` - Filter by age (current, 30_60, 60_90, 90_plus)
- `month` - Filter by month (1-12)
- `year` - Filter by year
- `quarter` - Filter by quarter (1-4)

## New API Endpoints

### Summary Endpoint
```
GET /api/debtors/transactions/summary/

Response:
[
    {
        "transaction_type": "IN",
        "count": 145,
        "total": 125000.00
    },
    {
        "transaction_type": "PM",
        "count": 98,
        "total": 95000.00
    },
    ...
]
```

### Monthly Trends Endpoint
```
GET /api/debtors/transactions/monthly_trends/

Response:
[
    {
        "month": "2024-01-01",
        "transaction_type": "IN",
        "count": 25,
        "total": 35000.00
    },
    {
        "month": "2024-01-01",
        "transaction_type": "PM",
        "count": 18,
        "total": 32000.00
    },
    ...
]
```

### Aging Summary Endpoint
```
GET /api/debtors/transactions/aging_summary/

Response:
{
    "current": 50000.00,
    "days_30_60": 25000.00,
    "days_60_90": 15000.00,
    "days_90_plus": 20000.00
}
```

### Debtor Summary Endpoint
```
GET /api/debtors/transactions/debtor_summary/

Response:
[
    {
        "debtor": 1001,
        "debtor__name": "ABC Trading",
        "outstanding": 15000.00,
        "transaction_count": 8
    },
    {
        "debtor": 1002,
        "debtor__name": "XYZ Stores",
        "outstanding": 8500.00,
        "transaction_count": 5
    },
    ...
]
```

## Practical Query Examples

### 1. Get All Unpaid Invoices for a Debtor
```python
debtor = Debtor.objects.get(customer_number=1001)
unpaid = DebtorTransaction.objects.filter(
    debtor=debtor,
    transaction_type='IN',
    is_allocated=False
).order_by('transaction_date')
```

### 2. Aging Analysis for Credit Management
```python
# Get aging analysis across all debtors
aging = DebtorTransaction.objects.aging_analysis()

# Get top 10 debtors with highest outstanding balance
top_debtors = DebtorTransaction.objects.filter(
    transaction_type__in=['IN', 'CS'],
    is_allocated=False
).values('debtor__name').annotate(
    outstanding=Sum('total_amount'),
    invoice_count=Count('id')
).order_by('-outstanding')[:10]
```

### 3. Monthly Sales by Debtor
```python
from datetime import date

# Sales for February 2024
feb_sales = DebtorTransaction.objects.invoices().filter(
    transaction_date__month=2,
    transaction_date__year=2024
).values('debtor__name').annotate(
    total_sales=Sum('total_amount'),
    invoice_count=Count('id')
).order_by('-total_sales')
```

### 4. POS vs Invoice Entry Analysis
```python
# Get transaction type distribution by source
source_analysis = DebtorTransaction.objects.values(
    'source_type',
    'transaction_type'
).annotate(
    count=Count('id'),
    total=Sum('total_amount')
).order_by('source_type', 'transaction_type')

# Just POS transactions
pos_txns = DebtorTransaction.objects.by_source('POS')

# Just imported transactions
import_txns = DebtorTransaction.objects.by_source('IMPORT')
```

### 5. Cash Flow Analysis
```python
# Calculate net cash flow for period
period_start = date(2024, 1, 1)
period_end = date(2024, 1, 31)

inbound = DebtorTransaction.objects.filter(
    transaction_type__in=['PM', 'RCP'],
    transaction_date__range=[period_start, period_end]
).aggregate(total=Sum('total_amount'))['total'] or 0

outbound_credits = DebtorTransaction.objects.filter(
    transaction_type__in=['CN', 'CR', 'RF'],
    transaction_date__range=[period_start, period_end]
).aggregate(total=Sum('total_amount'))['total'] or 0

net_cash_flow = inbound - outbound_credits
```

### 6. Reconciliation Reporting
```python
# Verify all batch import transactions
batch_id = 'BATCH-20240213-001'
batch_txns = DebtorTransaction.objects.filter(
    source_type='IMPORT',
    source_reference=batch_id
)

# Summary
summary = batch_txns.aggregate(
    count=Count('id'),
    total=Sum('total_amount'),
    by_type=Count('id')
)

# Detail by debtor
by_debtor = batch_txns.values('debtor__name').annotate(
    count=Count('id'),
    total=Sum('total_amount')
)
```

## Custom Manager Methods

All QuerySet methods are also available on the manager for convenience:

```python
# These are equivalent
DebtorTransaction.objects.invoices()
DebtorTransaction.objects.get_queryset().invoices()

# These are equivalent
DebtorTransaction.objects.aging_analysis()
DebtorTransaction.objects.get_queryset().aging_analysis()
```

## Database Indexes

Optimized indexes for common queries:

```
idx_deb_tran_date        - Debtor + Transaction Date (for debtor history)
idx_tran_type_date       - Transaction Type + Date (for reports)
idx_dtrano               - Transaction Number (for lookup)
idx_tran_status          - Status (for filtering)
idx_tran_source_type     - Source Type (for source tracking)
idx_tran_allocated       - Is Allocated (for A/R reporting)
idx_deb_alloc_date       - Debtor + Allocated + Date (combined filter)
```

## Migration

To apply these changes to your database:

```bash
python manage.py migrate debtors
```

The migration file `0011_debtortransaction_enhancements.py` will:
1. Add `source_type` field
2. Add `source_reference` field
3. Add `is_allocated` field
4. Create optimized indexes

## API Integration

The ViewSet automatically includes the new analysis endpoints:

```python
# In your urls.py, the router automatically registers:
GET /api/debtors/transactions/                    # List with filters
POST /api/debtors/transactions/                   # Create (read-only)
GET /api/debtors/transactions/{id}/               # Retrieve
GET /api/debtors/transactions/summary/            # Type summary
GET /api/debtors/transactions/monthly_trends/    # Monthly analysis
GET /api/debtors/transactions/aging_summary/     # Aging buckets
GET /api/debtors/transactions/debtor_summary/    # Outstanding by debtor
```

## Benefits

1. **Central Transaction Repository** - All debtor transactions in one place
2. **Source Tracking** - Know where each transaction originated
3. **Payment Tracking** - Track allocation status for A/R reporting
4. **Business Logic** - Convenient methods for common operations
5. **Performance** - Optimized indexes for quick queries
6. **Analysis** - Built-in aging and aggregation methods
7. **Flexibility** - Filter and aggregate for any custom report

## Next Steps

Consider adding:
- Transaction reconciliation logic
- Automatic interest calculation based on unallocated invoices
- Debtor credit scoring based on payment history
- Dunning management (automated follow-ups for overdue)
- Cash flow forecasting based on transaction history

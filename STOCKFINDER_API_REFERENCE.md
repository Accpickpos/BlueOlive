# Stockfinder API - Technical Reference

## API Base URL

```
https://api.accpick.com/api/
```

## Authentication Header

```
Authorization: ApiKey <api_key>
```

or

```
X-API-Key: <api_key>
```

---

## 1. Stock Control API

### GET /stock-control/stock-items/

List all stock items with pagination and filtering.

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20)
- `search` (string): Search by stock_code, description, or supplier_code
- `department` (integer): Filter by department
- `is_active` (boolean): Filter by active status

**Response:**
```json
{
  "count": 100,
  "next": "https://api.accpick.com/api/stock-control/stock-items/?page=2",
  "previous": null,
  "results": [
    {
      "stock_code": "SKU001",
      "description": "Product Name",
      "department": 1,
      "quantity_on_hand": 100.50,
      "cost_price": "150.00",
      "selling_price_1": "250.00",
      "selling_price_2": "260.00",
      "selling_price_3": "270.00",
      "is_active": true
    }
  ]
}
```

---

### POST /stock-control/stock-items/bulk_lookup/

Bulk lookup stock items by SKU codes.

**Request Body:**
```json
{
  "lookup_by": "stock_code|supplier_code",
  "values": ["SKU001", "SKU002"],
  "include_fields": [
    "stock_code",
    "description",
    "quantity_on_hand",
    "cost_price",
    "selling_price_1",
    "selling_price_2",
    "selling_price_3",
    "supplier_code"
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "stock_code": "SKU001",
      "description": "Product Name",
      "quantity_on_hand": 100.50,
      "cost_price": "150.00",
      "selling_price_1": "250.00"
    }
  ],
  "count": 1,
  "not_found": []
}
```

**Status Codes:**
- `200 OK`: Successful lookup
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Missing or invalid API key

---

### GET /stock-control/stock-items/search/

Advanced search with multiple criteria.

**Query Parameters:**
- `q` (string, required): Search query
- `type` (string): all|code|description|supplier_code
- `limit` (integer): Max results (default: 50)

**Response:**
```json
[
  {
    "stock_code": "SKU001",
    "description": "Product Name",
    "quantity_on_hand": 100.50,
    "cost_price": "150.00",
    "selling_price_1": "250.00"
  }
]
```

---

## 2. Invoices API

### GET /debtors/invoices/

List all invoices with filtering.

**Query Parameters:**
- `page` (integer): Page number
- `page_size` (integer): Items per page
- `status` (string): DRAFT|POSTED|PAID|PARTIAL_PAID|OVERDUE|CANCELLED
- `invoice_date__gte` (date): Filter by start date (YYYY-MM-DD)
- `invoice_date__lte` (date): Filter by end date (YYYY-MM-DD)
- `debtor` (integer): Filter by debtor ID
- `is_posted` (boolean): Filter by posted status

**Response:**
```json
{
  "count": 50,
  "next": "https://api.accpick.com/api/debtors/invoices/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "invoice_number": "INV001",
      "invoice_date": "2024-02-11",
      "debtor": 1,
      "debtor_name": "Customer Name",
      "total_amount": "1150.00",
      "amount_paid": "0.00",
      "status": "POSTED",
      "is_posted": true,
      "created_at": "2024-02-11T10:30:00Z"
    }
  ]
}
```

---

### POST /debtors/invoices/

Create a new invoice.

**Request Body:**
```json
{
  "invoice_number": "INV001",
  "invoice_date": "2024-02-11",
  "debtor": 1,
  "delivery_name": "John Doe",
  "delivery_address_line1": "123 Main St",
  "delivery_address_line2": "Apt 4B",
  "delivery_telephone": "555-1234",
  "order_number": "ORD001",
  "customer_reference": "REF001",
  "job_card_number": "JOB001",
  "sales_area": 1,
  "subtotal": "1000.00",
  "discount_amount": "0.00",
  "vat_amount": "150.00",
  "total_amount": "1150.00",
  "total_cost": "500.00",
  "gross_profit": "650.00",
  "lines": [
    {
      "line_number": 1,
      "stock_code": "SKU001",
      "description": "Product 1",
      "quantity": 5,
      "unit_price": "200.00",
      "discount_percentage": 0,
      "tax_code": 1,
      "line_total": "1000.00",
      "vat_amount": "150.00",
      "cost_price": "100.00",
      "line_profit": "900.00"
    }
  ]
}
```

**Response:**
```json
{
  "id": 1,
  "invoice_number": "INV001",
  "invoice_date": "2024-02-11",
  "debtor": 1,
  "debtor_name": "Customer Name",
  "total_amount": "1150.00",
  "status": "DRAFT",
  "is_posted": false
}
```

**Status Codes:**
- `201 Created`: Invoice created successfully
- `400 Bad Request`: Invalid data
- `401 Unauthorized`: Missing or invalid API key

---

### GET /debtors/invoices/{id}/

Get detailed invoice information.

**Response:**
```json
{
  "id": 1,
  "invoice_number": "INV001",
  "invoice_date": "2024-02-11",
  "debtor": 1,
  "debtor_name": "Customer Name",
  "delivery_name": "John Doe",
  "delivery_address_line1": "123 Main St",
  "delivery_address_line2": "Apt 4B",
  "delivery_telephone": "555-1234",
  "delivery_address_line1": "123 Main St",
  "order_number": "ORD001",
  "customer_reference": "REF001",
  "job_card_number": "JOB001",
  "sales_area": 1,
  "subtotal": "1000.00",
  "discount_amount": "0.00",
  "vat_amount": "150.00",
  "total_amount": "1150.00",
  "total_cost": "500.00",
  "gross_profit": "650.00",
  "status": "DRAFT",
  "is_posted": false,
  "amount_paid": "0.00",
  "paid_date": null,
  "is_cancelled": false,
  "lines": [
    {
      "id": 1,
      "line_number": 1,
      "stock_code": "SKU001",
      "description": "Product 1",
      "quantity": 5,
      "unit_price": "200.00",
      "discount_percentage": 0,
      "tax_code": 1,
      "line_total": "1000.00",
      "vat_amount": "150.00",
      "cost_price": "100.00",
      "line_profit": "900.00"
    }
  ],
  "created_at": "2024-02-11T10:30:00Z",
  "updated_at": "2024-02-11T10:30:00Z"
}
```

---

### POST /debtors/invoices/{id}/post_invoice/

Post invoice to debtor account.

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "status": "success",
  "message": "Invoice posted successfully",
  "invoice": { ... }
}
```

---

### POST /debtors/invoices/{id}/mark_as_paid/

Mark invoice as fully paid.

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "status": "success",
  "message": "Invoice marked as paid",
  "invoice": { ... }
}
```

---

### POST /debtors/invoices/{id}/cancel/

Cancel invoice.

**Request Body:**
```json
{
  "reason": "Customer requested cancellation"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Invoice cancelled successfully",
  "invoice": { ... }
}
```

---

### GET /debtors/invoices/by_debtor/

Get invoices for specific debtor.

**Query Parameters:**
- `debtor_id` (integer, required): Debtor number
- `status` (string, optional): Filter by status
- `page` (integer): Page number
- `page_size` (integer): Items per page

**Response:** Same as invoice list

---

### GET /debtors/invoices/by_date_range/

Get invoices within date range.

**Query Parameters:**
- `start_date` (date, required): Start date (YYYY-MM-DD)
- `end_date` (date, required): End date (YYYY-MM-DD)
- `page` (integer): Page number
- `page_size` (integer): Items per page

**Response:** Same as invoice list

---

## 3. Credit Notes API

### POST /pos/credit-notes/

Create a new credit note.

**Request Body:**
```json
{
  "credit_number": "CN001",
  "credit_date": "2024-02-11",
  "customer_name": "John Doe",
  "debtor_account": 1,
  "original_sale_number": "INV001",
  "reason": "Product returned",
  "sales_area": 1,
  "subtotal": "500.00",
  "vat_amount": "75.00",
  "total_amount": "575.00",
  "lines": [
    {
      "line_number": 1,
      "stock_code": "SKU001",
      "description": "Product 1",
      "quantity": 2,
      "unit_price": "250.00",
      "tax_code": 1,
      "line_total": "500.00",
      "vat_amount": "75.00",
      "cost_price": "100.00"
    }
  ]
}
```

**Response:**
```json
{
  "id": 1,
  "credit_number": "CN001",
  "credit_date": "2024-02-11",
  "customer_name": "John Doe",
  "total_amount": "575.00",
  "is_posted": false
}
```

---

### POST /pos/credit-notes/{id}/post_credit/

Post credit note and update stock.

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "status": "success",
  "message": "Credit note CN001 posted successfully"
}
```

---

## 4. Unified Document Search API

### GET /debtors/documents/search/

Search across all document types.

**Query Parameters:**
- `type` (string): invoice|credit_note|cash_sale|purchase_order|job_card|all
- `number` (string): Document number (partial match)
- `date_from` (date): Start date (YYYY-MM-DD)
- `date_to` (date): End date (YYYY-MM-DD)
- `debtor_id` (integer): Filter by debtor
- `status` (string): Document status

**Response:**
```json
{
  "invoices": [
    {
      "document_id": 1,
      "document_number": "INV001",
      "document_type": "invoice",
      "document_date": "2024-02-11",
      "customer": "John Doe",
      "amount": 1150.00,
      "status": "POSTED"
    }
  ],
  "credit_notes": [
    {
      "document_id": 1,
      "document_number": "CN001",
      "document_type": "credit_note",
      "document_date": "2024-02-11",
      "customer": "John Doe",
      "amount": 575.00,
      "status": "POSTED"
    }
  ],
  "cash_sales": [],
  "purchase_orders": [],
  "job_cards": [],
  "total_documents": 2
}
```

---

## 5. API Key Management API

### GET /settings/api-keys/

List all API keys.

**Query Parameters:**
- `status` (string): ACTIVE|INACTIVE|REVOKED
- `external_service` (string): Filter by service
- `page` (integer): Page number
- `page_size` (integer): Items per page

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "Stockfinder Integration",
      "external_service": "Stockfinder",
      "status": "ACTIVE",
      "last_used": "2024-02-11T15:30:00Z",
      "expires_at": "2025-12-31T23:59:59Z",
      "is_valid": true,
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

---

### POST /settings/api-keys/

Create a new API key.

**Request Body:**
```json
{
  "name": "Stockfinder Integration",
  "external_service": "Stockfinder",
  "description": "API key for Stockfinder integration",
  "allowed_endpoints": ["stock-items", "invoices"],
  "allowed_methods": ["GET", "POST"],
  "rate_limit_requests": 5000,
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Stockfinder Integration",
  "key": "secret_key_value_here",
  "external_service": "Stockfinder",
  "status": "ACTIVE",
  "is_valid": true
}
```

**Note:** The `key` is only returned at creation time. Store it securely!

---

### POST /settings/api-keys/{id}/revoke/

Revoke an API key.

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "status": "success",
  "message": "API key Stockfinder Integration revoked successfully"
}
```

---

### POST /settings/api-keys/{id}/activate/

Activate an API key.

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "status": "success",
  "message": "API key Stockfinder Integration activated successfully"
}
```

---

### POST /settings/api-keys/test_key/

Test an API key.

**Request Body:**
```json
{
  "key": "api_key_to_test"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "API key is valid",
  "data": {
    "is_valid": true,
    "name": "Stockfinder Integration",
    "external_service": "Stockfinder"
  }
}
```

---

## 6. Sales Orders / Job Cards API

### CLARIFICATION: Job Cards ARE Sales Orders

In this system, **Job Cards serve as Sales Orders**. They represent work orders/jobs to be performed and can be converted to invoices once completed. There is no separate SalesOrder model.

**Workflow:**
1. Create JobCard (ACTIVE status) = Sales Order Created
2. Complete the work
3. Convert to Invoice = Sales Order become billable invoice
4. Post Invoice = Record the transaction

---

### POST /pos/job-cards/

Create a new job card (sales order).

**Request Body:**
```json
{
  "job_number": "JOB-2024-001",
  "job_date": "2024-02-11",
  "customer_name": "John Doe",
  "address": "123 Main St",
  "telephone": "555-1234",
  "contact_person": "John Smith",
  "order_number": "ORD-12345",
  "registration_number": "ABC123",
  "job_description": "Repair and maintenance",
  "sales_area": 1,
  "operator_number": 101,
  "subtotal": "1000.00",
  "vat_amount": "150.00",
  "total_amount": "1150.00",
  "total_cost": "600.00",
  "gross_profit": "400.00",
  "status": "ACTIVE",
  "lines": [
    {
      "line_number": 1,
      "stock_code": "SKU001",
      "description": "Labor - 8 hours",
      "quantity": 8,
      "unit_price": "50.00",
      "discount_percentage": 0,
      "tax_code": 1,
      "line_total": "400.00",
      "vat_amount": "60.00",
      "cost_price": "200.00",
      "line_profit": "200.00"
    }
  ]
}
```

**Response:**
```json
{
  "id": 1,
  "job_number": "JOB-2024-001",
  "job_date": "2024-02-11",
  "customer_name": "John Doe",
  "status": "ACTIVE",
  "total_amount": "1150.00",
  "created_at": "2024-02-11T10:30:00Z"
}
```

**Status Codes:**
- `201 Created`: Job card created successfully
- `400 Bad Request`: Invalid data
- `401 Unauthorized`: Missing or invalid API key

---

### GET /pos/job-cards/

List all job cards.

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20)
- `status` (string): ACTIVE|INVOICED|CANCELLED
- `customer_name` (string): Search by customer
- `job_number` (string): Search by job number
- `job_date__gte` (date): Filter by start date (YYYY-MM-DD)
- `job_date__lte` (date): Filter by end date (YYYY-MM-DD)

**Response:**
```json
{
  "count": 50,
  "next": "https://api.accpick.com/api/pos/job-cards/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "job_number": "JOB-2024-001",
      "job_date": "2024-02-11",
      "customer_name": "John Doe",
      "status": "ACTIVE",
      "total_amount": "1150.00",
      "created_at": "2024-02-11T10:30:00Z"
    }
  ]
}
```

---

### GET /pos/job-cards/{id}/

Get detailed job card (sales order) information.

**Response:**
```json
{
  "id": 1,
  "job_number": "JOB-2024-001",
  "job_date": "2024-02-11",
  "customer_name": "John Doe",
  "address": "123 Main St",
  "telephone": "555-1234",
  "contact_person": "John Smith",
  "order_number": "ORD-12345",
  "registration_number": "ABC123",
  "job_description": "Repair and maintenance",
  "sales_area": 1,
  "operator_number": 101,
  "status": "ACTIVE",
  "subtotal": "1000.00",
  "vat_amount": "150.00",
  "total_amount": "1150.00",
  "total_cost": "600.00",
  "gross_profit": "400.00",
  "lines": [
    {
      "id": 1,
      "line_number": 1,
      "stock_code": "SKU001",
      "description": "Labor - 8 hours",
      "quantity": 8,
      "unit_price": "50.00",
      "discount_percentage": 0,
      "tax_code": 1,
      "line_total": "400.00",
      "vat_amount": "60.00",
      "cost_price": "200.00",
      "line_profit": "200.00"
    }
  ],
  "created_at": "2024-02-11T10:30:00Z",
  "updated_at": "2024-02-11T10:30:00Z"
}
```

---

### POST /pos/job-cards/{id}/convert_to_invoice/

Convert job card (sales order) to customer invoice. This is the key workflow - completing a job by converting it to an invoice for payment tracking.

**Request Body:**
```json
{
  "debtor_id": 5
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Job card converted to invoice",
  "invoice": {
    "id": 10,
    "invoice_number": "INV-20240211-00001",
    "invoice_date": "2024-02-11",
    "debtor_id": 5,
    "job_card_number": "JOB-2024-001",
    "subtotal": "1000.00",
    "vat_amount": "150.00",
    "total_amount": "1150.00",
    "status": "DRAFT",
    "is_posted": false,
    "lines": [
      {
        "id": 10,
        "line_number": 1,
        "stock_code": "SKU001",
        "description": "Labor - 8 hours",
        "quantity": 8,
        "unit_price": "50.00",
        "discount_percentage": 0,
        "tax_code": 1,
        "line_total": "400.00",
        "vat_amount": "60.00",
        "cost_price": "200.00",
        "line_profit": "200.00"
      }
    ]
  }
}
```

**Status Codes:**
- `201 Created`: Invoice created successfully
- `400 Bad Request`: Job card cannot be converted (already invoiced, cancelled, etc.)
- `404 Not Found`: Job card or debtor not found
- `401 Unauthorized`: Missing or invalid API key

**Important Notes:**
- Job card status changes to INVOICED after conversion
- Created invoice starts in DRAFT status
- You must POST the invoice before payment can be recorded

---

## 7. Purchase Orders API

### POST /purchase-orders/purchase-orders/

Automatically create a purchase order when an item is purchased via Stockfinder.

**Request Body:**
```json
{
  "po_number": "PO001",
  "po_date": "2024-02-11",
  "creditor": 5,
  "delivery_address": "Warehouse A",
  "required_delivery_date": "2024-02-18",
  "delivery_notes": "Please deliver before 5pm",
  "lines": [
    {
      "line_number": 1,
      "stock_code": "SKU001",
      "description": "Product 1",
      "quantity_ordered": 50,
      "quantity_received": 0,
      "unit_cost": "100.00",
      "tax_code": 1,
      "line_total": "5000.00"
    }
  ]
}
```

**Response:**
```json
{
  "id": 1,
  "po_number": "PO001",
  "po_date": "2024-02-11",
  "creditor": 5,
  "creditor_name": "Supplier Name",
  "status": "OPEN",
  "total_amount": "5000.00",
  "quantity_outstanding": 50,
  "created_at": "2024-02-11T10:30:00Z"
}
```

**Status Codes:**
- `201 Created`: Purchase order created successfully
- `400 Bad Request`: Invalid data or creditor not found
- `401 Unauthorized`: Missing or invalid API key

---

### GET /purchase-orders/purchase-orders/

List all purchase orders.

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20)
- `status` (string): OPEN|PARTIAL|COMPLETE|CANCELLED|CLOSED
- `creditor` (integer): Filter by creditor
- `po_date__gte` (date): Filter by start date (YYYY-MM-DD)
- `po_date__lte` (date): Filter by end date (YYYY-MM-DD)
- `is_posted` (boolean): Filter by posted status

**Response:**
```json
{
  "count": 40,
  "next": "https://api.accpick.com/api/purchase-orders/purchase-orders/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "po_number": "PO001",
      "po_date": "2024-02-11",
      "creditor": 5,
      "creditor_name": "Supplier Name",
      "status": "OPEN",
      "total_amount": "5000.00",
      "quantity_outstanding": 50,
      "is_posted": false,
      "created_at": "2024-02-11T10:30:00Z"
    }
  ]
}
```

---

### GET /purchase-orders/purchase-orders/{id}/

Get detailed purchase order information.

**Response:**
```json
{
  "id": 1,
  "po_number": "PO001",
  "po_date": "2024-02-11",
  "creditor": 5,
  "creditor_name": "Supplier Name",
  "creditor_contact": "supplier@example.com",
  "delivery_address": "Warehouse A",
  "required_delivery_date": "2024-02-18",
  "delivery_notes": "Please deliver before 5pm",
  "status": "OPEN",
  "total_amount": "5000.00",
  "is_posted": false,
  "lines": [
    {
      "id": 1,
      "line_number": 1,
      "stock_code": "SKU001",
      "description": "Product 1",
      "quantity_ordered": 50,
      "quantity_received": 0,
      "quantity_outstanding": 50,
      "unit_cost": "100.00",
      "tax_code": 1,
      "line_total": "5000.00"
    }
  ],
  "created_at": "2024-02-11T10:30:00Z",
  "updated_at": "2024-02-11T10:30:00Z"
}
```

---

### POST /purchase-orders/purchase-orders/{id}/post_po/

Post purchase order to creditor account.

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "status": "success",
  "message": "Purchase order PO001 posted successfully",
  "purchase_order": { ... }
}
```

---

### POST /purchase-orders/purchase-orders/{id}/receive-stock/

Receive stock against a purchase order line.

**Request Body:**
```json
{
  "lines": [
    {
      "line_id": 1,
      "quantity_received": 25,
      "reference_number": "GRN001"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Stock received successfully",
  "lines_updated": 1,
  "stock_updated": true
}
```

---

### POST /purchase-orders/purchase-orders/{id}/cancel/

Cancel a purchase order.

**Request Body:**
```json
{
  "reason": "Supplier out of stock"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Purchase order PO001 cancelled successfully",
  "purchase_order": { ... }
}
```

---

### GET /purchase-orders/purchase-orders/by_creditor/

Get purchase orders for specific creditor.

**Query Parameters:**
- `creditor_id` (integer, required): Creditor number
- `status` (string, optional): Filter by status
- `page` (integer): Page number
- `page_size` (integer): Items per page

**Response:** Same as purchase orders list

---

### GET /purchase-orders/purchase-orders/by_date_range/

Get purchase orders within date range.

**Query Parameters:**
- `start_date` (date, required): Start date (YYYY-MM-DD)
- `end_date` (date, required): End date (YYYY-MM-DD)
- `page` (integer): Page number
- `page_size` (integer): Items per page

**Response:** Same as purchase orders list

---

## Error Responses

### 400 Bad Request

```json
{
  "status": "error",
  "message": "Validation failed",
  "details": {
    "invoice_number": ["This field is required."],
    "total_amount": ["Ensure that the total is greater than zero."]
  }
}
```

### 401 Unauthorized

```json
{
  "status": "error",
  "message": "API key authentication failed. Invalid or missing API key."
}
```

### 403 Forbidden

```json
{
  "status": "error",
  "message": "API key does not have access to this endpoint."
}
```

### 404 Not Found

```json
{
  "status": "error",
  "message": "Resource not found."
}
```

### 429 Too Many Requests

```json
{
  "status": "error",
  "message": "Rate limit exceeded. Maximum 1000 requests per hour."
}
```

---

## Data Types and Formats

### Dates
Format: `YYYY-MM-DD`  
Example: `2024-02-11`

### DateTime
Format: `ISO 8601 with Z timezone`  
Example: `2024-02-11T15:30:00Z`

### Decimals
Format: Quoted string with up to 2 decimal places  
Example: `"1150.00"`

### Boolean
Format: `true` or `false`  
Example: `true`

---

## Rate Limiting Headers

All responses include:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1707600000
```

Where:
- `X-RateLimit-Limit`: Total requests per hour
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp of window reset

---

**Last Updated:** February 11, 2026  
**Version:** 2.0

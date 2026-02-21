# Stockfinder API Integration - Complete Implementation Guide

## Overview

This document provides a comprehensive guide for integrating the Accpick ERP system with Stockfinder using the newly implemented API endpoints and authentication system.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Integration Examples](#integration-examples)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Create an API Key

**Endpoint:** `POST /api/settings/api-keys/`

**Request:**
```json
{
  "name": "Stockfinder Integration",
  "external_service": "Stockfinder",
  "description": "API key for Stockfinder integration",
  "allowed_endpoints": ["stock-items", "invoices", "credit-notes", "documents"],
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
  "key": "your_secret_api_key_here",
  "external_service": "Stockfinder",
  "status": "ACTIVE",
  "is_valid": true
}
```

**Important:** Store the `key` value securely! You won't be able to retrieve it again.

### 2. Test the API Key

**Endpoint:** `POST /api/settings/api-keys/test_key/`

**Request:**
```json
{
  "key": "your_secret_api_key_here"
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

## Authentication

### Using API Keys

All API requests must include authentication via one of these methods:

#### Method 1: Authorization Header (Recommended)
```bash
curl -H "Authorization: ApiKey your_secret_api_key_here" \
  https://api.accpick.com/api/stock-control/stock-items/
```

#### Method 2: X-API-Key Header
```bash
curl -H "X-API-Key: your_secret_api_key_here" \
  https://api.accpick.com/api/stock-control/stock-items/
```

#### Method 3: Python Requests
```python
import requests

headers = {
    "Authorization": "ApiKey your_secret_api_key_here"
}

response = requests.get(
    "https://api.accpick.com/api/stock-control/stock-items/",
    headers=headers
)
```

#### Method 4: JavaScript Fetch
```javascript
const headers = {
    "Authorization": "ApiKey your_secret_api_key_here",
    "Content-Type": "application/json"
};

fetch("https://api.accpick.com/api/stock-control/stock-items/", {
    method: "GET",
    headers: headers
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## API Endpoints

### 1. Stock Load - Stock Items

#### Bulk Stock Lookup (NEW ENDPOINT)

**Endpoint:** `POST /api/stock-control/stock-items/bulk_lookup/`

**Description:** Query specific stock items by SKU code

**Request:**
```json
{
  "lookup_by": "stock_code",
  "values": ["SKU001", "SKU002", "SKU003"],
  "include_fields": ["stock_code", "description", "quantity_on_hand", "cost_price", "selling_price_1"]
}
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "stock_code": "SKU001",
      "description": "Product 1",
      "quantity_on_hand": 100.5,
      "cost_price": "150.00",
      "selling_price_1": "250.00"
    },
    {
      "stock_code": "SKU002",
      "description": "Product 2",
      "quantity_on_hand": 50.0,
      "cost_price": "200.00",
      "selling_price_1": "350.00"
    }
  ],
  "count": 2
}
```

#### Search Stock Items

**Endpoint:** `GET /api/stock-control/stock-items/search/?q=product&type=all`

**Parameters:**
- `q` (required): Search query
- `type` (optional): `all`, `code`, `description`, `supplier_code`

**Response:**
```json
[
  {
    "id": "SKU001",
    "stock_code": "SKU001",
    "description": "Product 1",
    "quantity_on_hand": 100.5,
    "cost_price": "150.00",
    "selling_price_1": "250.00"
  }
]
```

---

### 2. Invoices - Document Management

#### Create Invoice (NEW ENDPOINT)

**Endpoint:** `POST /api/debtors/invoices/`

**Request:**
```json
{
  "invoice_number": "INV001",
  "invoice_date": "2024-02-11",
  "debtor": 1,
  "delivery_name": "John Doe",
  "delivery_address_line1": "123 Main St",
  "order_number": "ORD001",
  "subtotal": 1000.00,
  "vat_amount": 150.00,
  "total_amount": 1150.00,
  "lines": [
    {
      "line_number": 1,
      "stock_code": "SKU001",
      "description": "Product 1",
      "quantity": 5,
      "unit_price": 200.00,
      "tax_code": 1,
      "line_total": 1000.00,
      "vat_amount": 150.00,
      "cost_price": 100.00
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
  "debtor_name": "Customer Name",
  "total_amount": "1150.00",
  "status": "DRAFT",
  "is_posted": false
}
```

#### List Invoices

**Endpoint:** `GET /api/debtors/invoices/?status=POSTED&invoice_date__gte=2024-01-01`

**Query Parameters:**
- `status`: DRAFT, POSTED, PAID, PARTIAL_PAID, OVERDUE, CANCELLED
- `invoice_date__gte`: Start date
- `invoice_date__lte`: End date
- `debtor`: Filter by debtor ID

#### Retrieve Invoice Details

**Endpoint:** `GET /api/debtors/invoices/{id}/`

**Response includes:**
- Invoice header information
- All line items with pricing
- Current status and balance

#### Post Invoice

**Endpoint:** `POST /api/debtors/invoices/{id}/post_invoice/`

Transitions invoice from DRAFT to POSTED status and creates debtor transaction.

#### Mark as Paid

**Endpoint:** `POST /api/debtors/invoices/{id}/mark_as_paid/`

Marks invoice as fully paid.

#### Cancel Invoice

**Endpoint:** `POST /api/debtors/invoices/{id}/cancel/`

**Request:**
```json
{
  "reason": "Customer requested cancellation"
}
```

---

### 3. Credit Notes - Returns Management

#### Create Credit Note

**Endpoint:** `POST /api/pos/credit-notes/`

**Request:**
```json
{
  "credit_number": "CN001",
  "credit_date": "2024-02-11",
  "customer_name": "John Doe",
  "original_sale_number": "INV001",
  "reason": "Product returned",
  "subtotal": 500.00,
  "vat_amount": 75.00,
  "total_amount": 575.00,
  "lines": [
    {
      "line_number": 1,
      "stock_code": "SKU001",
      "description": "Product 1",
      "quantity": 2,
      "unit_price": 250.00,
      "tax_code": 1,
      "line_total": 500.00,
      "vat_amount": 75.00
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
  "total_amount": "575.00",
  "is_posted": false
}
```

#### Post Credit Note

**Endpoint:** `POST /api/pos/credit-notes/{id}/post_credit/`

Posts credit note and updates stock levels.

---

### 4. Job Cards - Sales Orders Management

**IMPORTANT:** Job Cards serve as **Sales Orders** in the system. They represent work orders/jobs that need to be performed and can be converted to invoices once completed.

#### Create Job Card (Sales Order)

**Endpoint:** `POST /api/pos/job-cards/`

**Request:**
```json
{
  "job_number": "JOB-2024-001",
  "job_date": "2024-02-11",
  "customer_name": "Acme Corporation",
  "address": "123 Business Street",
  "telephone": "0123456789",
  "contact_person": "John Smith",
  "order_number": "ORD-12345",
  "registration_number": "ABC123",
  "job_description": "Repair and maintenance",
  "sales_area": 1,
  "operator_number": 101,
  "subtotal": 1000.00,
  "vat_amount": 150.00,
  "total_amount": 1150.00,
  "total_cost": 600.00,
  "gross_profit": 400.00,
  "status": "ACTIVE",
  "lines": [
    {
      "line_number": 1,
      "stock_code": "PART-001",
      "description": "Labor - 8 hours @ 50/hr",
      "quantity": 8,
      "unit_price": 50.00,
      "discount_percentage": 0,
      "tax_code": 1,
      "line_total": 400.00,
      "vat_amount": 60.00,
      "cost_price": 200.00,
      "line_profit": 200.00
    },
    {
      "line_number": 2,
      "stock_code": "SKU-002",
      "description": "Replacement Parts",
      "quantity": 1,
      "unit_price": 600.00,
      "discount_percentage": 0,
      "tax_code": 1,
      "line_total": 600.00,
      "vat_amount": 90.00,
      "cost_price": 400.00,
      "line_profit": 200.00
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
  "customer_name": "Acme Corporation",
  "total_amount": "1150.00",
  "status": "ACTIVE",
  "lines": [...]
}
```

#### List Job Cards

**Endpoint:** `GET /api/pos/job-cards/?status=ACTIVE&job_date__gte=2024-02-01`

**Query Parameters:**
- `status`: ACTIVE, INVOICED, CANCELLED
- `job_date__gte` / `job_date__lte`: Date range filtering
- `customer_name`: Search by customer
- `job_number`: Search by job number

#### Convert Job Card to Invoice

**IMPORTANT:** This is the key workflow! Once a job card is completed, convert it to an invoice to record the sale and allow for payment tracking.

**Endpoint:** `POST /api/pos/job-cards/{id}/convert_to_invoice/`

**Request:**
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
    "lines": [...]
  }
}
```

**Workflow:**
1. Create Job Card (ACTIVE status)
2. Complete the work
3. Convert to Invoice (creates DRAFT invoice)
4. Post Invoice (POSTED status)
5. Track payments

---

### 5. Unified Document Search (NEW ENDPOINT)

**Endpoint:** `GET /api/debtors/documents/search/?type=all&date_from=2024-01-01&date_to=2024-12-31`

**Query Parameters:**
- `type`: invoice, credit_note, cash_sale, purchase_order, job_card, all
- `number`: Document number (partial match allowed)
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)
- `debtor_id`: Filter by debtor
- `status`: Document status

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

### 5. Purchase Orders

#### Create Purchase Order (EXISTING)

**Endpoint:** `POST /api/purchase-orders/purchase-orders/`

Fully compatible with Stockfinder requirements.

---

## Integration Examples

### Example 1: Complete Stock Load Integration

```python
import requests
from datetime import datetime, timedelta

class StockfinderIntegration:
    def __init__(self, api_key, base_url="https://api.accpick.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_stock_items(self, stock_codes):
        """Get stock items by SKU codes"""
        endpoint = f"{self.base_url}/api/stock-control/stock-items/bulk_lookup/"
        payload = {
            "lookup_by": "stock_code",
            "values": stock_codes,
            "include_fields": [
                "stock_code",
                "description",
                "quantity_on_hand",
                "cost_price",
                "selling_price_1",
                "selling_price_2",
                "selling_price_3"
            ]
        }
        
        response = requests.post(endpoint, json=payload, headers=self.headers)
        if response.status_code == 200:
            return response.json()["data"]
        else:
            raise Exception(f"Error: {response.text}")
    
    def search_invoices(self, date_from, date_to, debtor_id=None):
        """Search invoices by date range"""
        endpoint = f"{self.base_url}/api/debtors/invoices/"
        params = {
            "invoice_date__gte": date_from,
            "invoice_date__lte": date_to,
            "status": "POSTED"
        }
        
        if debtor_id:
            params["debtor"] = debtor_id
        
        response = requests.get(endpoint, params=params, headers=self.headers)
        if response.status_code == 200:
            return response.json()["results"]
        else:
            raise Exception(f"Error: {response.text}")
    
    def unified_document_search(self, doc_type="all", date_from=None, date_to=None):
        """Search across all document types"""
        endpoint = f"{self.base_url}/api/debtors/documents/search/"
        params = {
            "type": doc_type
        }
        
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        response = requests.get(endpoint, params=params, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.text}")


# Usage Example
integration = StockfinderIntegration("your_api_key_here")

# Get stocks
stocks = integration.get_stock_items(["SKU001", "SKU002", "SKU003"])
print("Stock Items:", stocks)

# Search invoices from last 30 days
today = datetime.now().date()
thirty_days_ago = today - timedelta(days=30)
invoices = integration.search_invoices(
    date_from=str(thirty_days_ago),
    date_to=str(today)
)
print("Recent Invoices:", invoices)

# Unified search
documents = integration.unified_document_search(
    doc_type="all",
    date_from=str(thirty_days_ago),
    date_to=str(today)
)
print("All Documents:", documents)
```

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | Request processed successfully |
| 400 | Bad Request | Check request parameters and format |
| 401 | Unauthorized | Invalid or missing API key |
| 403 | Forbidden | API key doesn't have access to this endpoint |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limited | Too many requests, wait before retrying |
| 500 | Server Error | Contact support |

### Error Response Format

```json
{
  "status": "error",
  "message": "Description of what went wrong",
  "details": {
    "field": ["Error message for field"]
  }
}
```

---

## Rate Limiting

API keys have configurable rate limits:

- **Default:** 1000 requests per hour
- **Window:** 3600 seconds (1 hour)
- **Headers:** Include `X-RateLimit-Limit` and `X-RateLimit-Remaining`

### Handling Rate Limits

```python
import time

def make_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            # Rate limited, wait before retrying
            wait_time = 60  # wait 60 seconds
            print(f"Rate limited. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

---

## Troubleshooting

### Issue: "Invalid API key"

**Cause:** API key is invalid or doesn't exist  
**Solution:** 
1. Verify the API key value
2. Check that the key hasn't been revoked
3. Create a new API key if needed

### Issue: "API key is not valid or has expired"

**Cause:** API key is inactive or has expired  
**Solution:**
1. Check API key status in admin panel
2. Verify expiration date
3. Activate the key if it's inactive

### Issue: "Rate limit exceeded"

**Cause:** Too many requests in the time window  
**Solution:**
1. Implement exponential backoff in your code
2. Request a higher rate limit
3. Batch requests efficiently

### Issue: "Endpoint not found"

**Cause:** Wrong API path or version  
**Solution:**
1. Check the API endpoint documentation
2. Verify the API base URL
3. Check HTTP method (GET vs POST)

---

## Support

For issues or questions regarding the API integration:

- **Email:** support@accpick.com
- **Documentation:** https://api.accpick.com/docs/
- **Status Page:** https://status.accpick.com/

---

## API Key Management Best Practices

1. **Security:**
   - Store API keys securely (use environment variables)
   - Never commit API keys to version control
   - Rotate keys regularly
   - Use different keys for different systems

2. **Monitoring:**
   - Monitor API key usage in the admin panel
   - Set up alerts for unusual activity
   - Review key access logs regularly

3. **Access Control:**
   - Limit endpoints per key
   - Restrict HTTP methods (GET-only for read operations)
   - Set appropriate expiration dates
   - Revoke unused keys

---

**Last Updated:** February 11, 2025  
**Version:** 1.0

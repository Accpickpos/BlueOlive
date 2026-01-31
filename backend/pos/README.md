# FastAPI Point of Sale System

FastAPI-based Point of Sale system integrated with Django REST Framework backend and Next.js frontend.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Django backend running on http://localhost:8000
- Next.js frontend running on http://localhost:3000

### Installation

1. **Navigate to POS directory**
   ```bash
   cd backend/pos
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize database**
   ```bash
   python -c "from database import init_db; init_db()"
   ```

6. **Run the application**
   ```bash
   uvicorn main:app --host 127.0.0.1 --port 8001 --reload
   ```

Visit http://localhost:8001/docs for interactive API documentation.

## Architecture

### Microservices Integration
- **FastAPI** (Port 8001): Transaction processing (invoices, sales, receipts, etc.)
- **Django DRF** (Port 8000): Master data management (debtors, stock, creditors)
- **Next.js** (Port 3000): Frontend interface

### Key Components

#### Services
- `drf_integration.py`: Async communication with Django backend
- `calculation_service.py`: Financial calculations (tax, discounts, profits)
- `number_generator.py`: Thread-safe transaction number generation

#### Routers (API Endpoints)
- **invoices**: Invoice management with stock and debtor integration
- **cash_sales**: Cash transactions with tender routine and rounding
- **credit_notes**: Credit note processing
- **receipts**: Receipt on account with PDC support
- **cash_returns**: Cash return handling
- **laybyes**: Laybye lifecycle management
- **quotations**: Quote management and conversion to invoices
- **job_costing**: Job card and costing
- **repair_controls**: Repair voucher workflow
- **payouts**: Cash payout tracking
- **cash_control**: Cashier reconciliation
- **transaction_query**: Search and reporting

## Configuration

### Environment Variables
```
DATABASE_URL=postgresql://user:password@localhost:5432/blueolive
DRF_BASE_URL=http://localhost:8000/api
FASTAPI_PORT=8001
DEBUG=False
```

See `.env.example` for all available options.

## API Examples

### Create Invoice
```bash
curl -X POST http://localhost:8001/api/v1/invoices/ \
  -H "Content-Type: application/json" \
  -d '{
    "debtor_account_number": "D001",
    "invoice_date": "2024-01-27T00:00:00",
    "line_items": [
      {
        "item_code": "ITEM001",
        "description": "Product",
        "quantity": 2,
        "cost_price": 100,
        "selling_price": 150,
        "discount_percentage": 0,
        "tax_code": "STANDARD"
      }
    ]
  }'
```

### Create Cash Sale
```bash
curl -X POST http://localhost:8001/api/v1/cash-sales/ \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_date": "2024-01-27T00:00:00",
    "line_items": [...],
    "tenders": [
      {
        "tender_type": "CASH",
        "amount": 400
      }
    ]
  }'
```

### List Invoices
```bash
curl http://localhost:8001/api/v1/invoices/?skip=0&limit=10
```

## Database Models

### Core Models
- `Invoice` / `InvoiceLineItem`: Invoice transactions
- `CashSale` / `CashSaleLineItem` / `CashSaleTender`: Cash sales
- `CreditNote` / `CreditNoteLineItem`: Credit notes
- `Receipt` / `ReceiptTender`: Receipt on account
- `Laybye` / `LaybeyLineItem` / `LaybeyPayment`: Laybye management
- `Quotation` / `QuotationLineItem`: Sales quotations
- `JobCosting` / `JobCostingLineItem`: Job cards
- `RepairControl`: Repair vouchers
- `Payout`: Cash payouts
- `CashControl`: Reconciliation records
- `TransactionLog`: Audit trail

## DRF Backend Integration

The FastAPI system integrates with Django backend for:

1. **Debtor Operations**
   - Get debtor information
   - Get debtor balance
   - Post transactions to debtor account

2. **Stock Operations**
   - Get stock item details
   - Check available quantity
   - Update stock quantities

3. **Cashbook Operations**
   - Post cash receipts and payouts
   - Track cash flow

4. **Configuration**
   - Get tax rates
   - Get system configuration

## Development

### Running Tests
```bash
pytest
```

### Running with Docker
```bash
docker-compose up
```

### Database Migrations (Alembic)
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Performance Optimization

- Database connection pooling
- Async operations for external API calls
- Query optimization with indexes
- Response caching available
- Load testing with Locust

## Security

- Input validation via Pydantic
- SQL injection prevention via ORM
- CORS configured for frontend
- Environment-based secrets
- Ready for JWT authentication

## Implementation Status

### Fully Implemented (2 modules)
✅ **invoices.py** - Complete invoice management
✅ **cash_sales.py** - Complete cash sale processing

### Placeholder (10 modules)
- credit_notes.py
- receipts.py
- cash_returns.py
- laybyes.py
- quotations.py
- job_costing.py
- repair_controls.py
- payouts.py
- cash_control.py
- transaction_query.py

Each placeholder follows the same pattern as invoices.py and can be implemented following that structure.

## Project Structure
```
backend/pos/
├── main.py                 # FastAPI application entry point
├── models.py              # Pydantic models for request/response
├── database.py            # SQLAlchemy models and configuration
├── config.py              # Application settings
├── requirements.txt       # Python dependencies
├── routers/               # API route handlers
│   ├── invoices.py
│   ├── cash_sales.py
│   ├── credit_notes.py
│   └── ... (10 more)
├── services/              # Business logic
│   ├── drf_integration.py
│   ├── calculation_service.py
│   └── number_generator.py
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Contributing

1. Follow existing code patterns
2. Add type hints
3. Include docstrings
4. Add tests for new features
5. Update documentation

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the architecture diagrams in the main workspace
3. Check Django backend logs for integration issues
4. Monitor network requests between FastAPI and Django

## Next Steps

To complete the implementation:
1. Implement remaining 10 router modules
2. Add comprehensive error handling
3. Implement audit logging
4. Add integration tests
5. Set up monitoring and alerting
6. Performance testing and optimization

## License

MIT License - Free to use and modify

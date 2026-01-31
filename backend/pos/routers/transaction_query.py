"""Placeholder routers - to be implemented"""

from fastapi import APIRouter

# Transaction Query Router
router = APIRouter(prefix="/api/v1/transaction-query", tags=["transaction_query"])

# TODO: Implement transaction query endpoints
# - GET /search : Search transactions (by number, date, etc.)
# - GET /reprint/{transaction_number} : Get transaction for reprinting
# - GET /report : Generate transaction reports

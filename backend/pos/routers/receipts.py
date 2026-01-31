"""Placeholder routers - to be implemented"""

from fastapi import APIRouter

# Receipts Router
router = APIRouter(prefix="/api/v1/receipts", tags=["receipts"])

# TODO: Implement receipt endpoints
# - POST / : Create receipt (balance forward, open item, PDC)
# - GET /{id} : Get receipt details
# - GET / : List receipts
# - PUT /{id} : Update receipt
# - POST /{id}/post : Post receipt
# - DELETE /{id} : Delete draft receipt

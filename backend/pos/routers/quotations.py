"""Placeholder routers - to be implemented"""

from fastapi import APIRouter

# Quotations Router
router = APIRouter(prefix="/api/v1/quotations", tags=["quotations"])

# TODO: Implement quotation endpoints
# - POST / : Create quotation
# - GET /{id} : Get quotation details
# - GET / : List quotations
# - PUT /{id} : Update quotation
# - POST /{id}/post : Post quotation
# - POST /{id}/convert : Convert to invoice
# - DELETE /{id} : Delete draft quotation

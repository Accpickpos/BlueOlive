"""Placeholder routers - to be implemented"""

from fastapi import APIRouter

# Cash Returns Router
router = APIRouter(prefix="/api/v1/cash-returns", tags=["cash_returns"])

# TODO: Implement cash return endpoints
# - POST / : Create cash return
# - GET /{id} : Get cash return details
# - GET / : List cash returns
# - PUT /{id} : Update cash return
# - POST /{id}/post : Post cash return
# - DELETE /{id} : Delete draft cash return

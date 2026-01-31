"""Placeholder routers - to be implemented"""

from fastapi import APIRouter

# Cash Control Router
router = APIRouter(prefix="/api/v1/cash-control", tags=["cash_control"])

# TODO: Implement cash control endpoints
# - POST / : Create cash control/reconciliation
# - GET /{id} : Get cash control details
# - GET / : List cash controls
# - PUT /{id} : Update cash control
# - POST /{id}/post : Post cash control
# - DELETE /{id} : Delete draft cash control

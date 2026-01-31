"""Placeholder routers - to be implemented"""

from fastapi import APIRouter

# Credit Notes Router
router = APIRouter(prefix="/api/v1/credit-notes", tags=["credit_notes"])

# TODO: Implement credit notes endpoints
# - POST / : Create credit note (from invoice or not)
# - GET /{id} : Get credit note details
# - GET / : List credit notes
# - PUT /{id} : Update credit note
# - POST /{id}/post : Post credit note
# - DELETE /{id} : Delete draft credit note

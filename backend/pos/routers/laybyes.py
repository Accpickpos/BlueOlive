"""Placeholder routers - to be implemented"""

from fastapi import APIRouter

# Laybyes Router
router = APIRouter(prefix="/api/v1/laybyes", tags=["laybyes"])

# TODO: Implement laybye endpoints
# - POST / : Create laybye
# - GET /{id} : Get laybye details
# - GET / : List laybyes
# - PUT /{id} : Update laybye
# - POST /{id}/post : Post laybye
# - POST /{id}/payments : Add payment to laybye
# - POST /{id}/complete : Complete laybye
# - DELETE /{id} : Delete draft laybye

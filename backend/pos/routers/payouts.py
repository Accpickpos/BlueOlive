"""Placeholder routers - to be implemented"""

from fastapi import APIRouter

# Payouts Router
router = APIRouter(prefix="/api/v1/payouts", tags=["payouts"])

# TODO: Implement payout endpoints
# - POST / : Create payout
# - GET /{id} : Get payout details
# - GET / : List payouts
# - PUT /{id} : Update payout
# - POST /{id}/post : Post payout
# - DELETE /{id} : Delete draft payout

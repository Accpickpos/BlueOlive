"""Placeholder routers - to be implemented"""

from fastapi import APIRouter

# Job Costing Router
router = APIRouter(prefix="/api/v1/job-costing", tags=["job_costing"])

# TODO: Implement job costing endpoints
# - POST / : Create job card
# - GET /{id} : Get job card details
# - GET / : List job cards
# - PUT /{id} : Update job card
# - POST /{id}/post : Post job card
# - DELETE /{id} : Delete draft job card

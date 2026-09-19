from fastapi import APIRouter
from app.api.v1 import assistant, health, knowledge, memberships, organizations, users

api_router = APIRouter()

# Health endpoints
api_router.include_router(health.router, tags=["Health"])

# Core Data Access Layer endpoints
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(
    memberships.router,
    prefix="/organizations/{organization_id}/members",
    tags=["Memberships"],
)
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["Assistant"])

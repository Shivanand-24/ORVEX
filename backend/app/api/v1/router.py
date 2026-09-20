from fastapi import APIRouter
from app.api.v1 import agents, assistant, executions, health, knowledge, memberships, organizations, users, workflows

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
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(executions.router, tags=["Executions"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])

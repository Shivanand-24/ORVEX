from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, NotFoundError
from app.models.agent import Agent
from app.repositories.agent_repository import agent_repository


class AgentResolver:
    """Resolves and validates Agent configurations for execution."""

    async def resolve_for_execution(
        self,
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID,
    ) -> Agent:
        """Resolves an agent and enforces existence, tenant ownership, and active state."""
        agent = await agent_repository.get_by_id(db, agent_id, load_relationships=True)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        # Enforce strict multi-tenant isolation
        if agent.organization_id != organization_id:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        # Enforce active operational status
        if agent.status != "Active":
            raise BadRequestError(
                f"Cannot execute agent '{agent.name}' ({agent_id}) because its status is '{agent.status}'. "
                "Only 'Active' agents can be executed."
            )

        return agent


agent_resolver = AgentResolver()

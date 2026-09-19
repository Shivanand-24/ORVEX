from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, NotFoundError
from app.models.agent import Agent
from app.repositories.agent_repository import agent_repository
from app.repositories.knowledge_source_repository import knowledge_source_repository
from app.repositories.membership_repository import membership_repository
from app.repositories.organization_repository import organization_repository
from app.repositories.user_repository import user_repository
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate
from app.schemas.knowledge import KnowledgeSourceResponse


class AgentService:
    """Business logic, tenant isolation, relationship verification, and transaction boundaries for Agents."""

    @staticmethod
    def _to_agent_response(agent: Agent) -> AgentResponse:
        tools = [t.tool_name for t in agent.tools] if agent.tools else []
        ks_ids = [ks.id for ks in agent.knowledge_sources] if agent.knowledge_sources else []
        owner = agent.creator.full_name if agent.creator else None

        return AgentResponse(
            id=agent.id,
            organization_id=agent.organization_id,
            created_by_user_id=agent.created_by_user_id,
            name=agent.name,
            description=agent.description,
            domain=agent.domain,
            status=agent.status,
            system_instructions=agent.system_instructions,
            require_approval=agent.require_approval,
            tools=tools,
            knowledge_source_ids=ks_ids,
            owner=owner,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            executions=0,
            success_rate="100%",
            last_run="Never",
        )

    async def create_agent(
        self, db: AsyncSession, schema: AgentCreate
    ) -> AgentResponse:
        # Validate organization existence
        org = await organization_repository.get_by_id(db, schema.organization_id)
        if not org:
            raise NotFoundError(f"Organization with ID '{schema.organization_id}' not found.")

        # Resolve or validate created_by_user_id
        user_id = schema.created_by_user_id
        if user_id is not None:
            user = await user_repository.get_by_id(db, user_id)
            if not user:
                raise NotFoundError(f"User with ID '{user_id}' not found.")
        else:
            # Fallback to first member of organization
            members = await membership_repository.list_by_organization(db, schema.organization_id, limit=1)
            if members:
                user_id = members[0].user_id
            else:
                # Fallback to any registered user
                users = await user_repository.list(db, limit=1)
                if users:
                    user_id = users[0].id
                else:
                    raise BadRequestError(
                        "created_by_user_id is required to create an agent when no registered user exists."
                    )

        # Validate initial knowledge sources belong to the same organization
        if schema.knowledge_source_ids:
            for ks_id in schema.knowledge_source_ids:
                ks = await knowledge_source_repository.get_by_id(db, ks_id)
                if not ks or ks.organization_id != schema.organization_id:
                    raise NotFoundError(f"Knowledge Source with ID '{ks_id}' not found.")

        # Create Agent
        agent = await agent_repository.create(
            db=db,
            organization_id=schema.organization_id,
            created_by_user_id=user_id,
            name=schema.name,
            description=schema.description,
            domain=schema.domain,
            status=schema.status,
            system_instructions=schema.system_instructions,
            require_approval=schema.require_approval,
        )

        # Attach initial tools
        if schema.tools:
            for tool_name in schema.tools:
                await agent_repository.add_tool(db, agent.id, tool_name)

        # Attach initial knowledge sources
        if schema.knowledge_source_ids:
            for ks_id in schema.knowledge_source_ids:
                await agent_repository.add_knowledge_source(db, agent.id, ks_id)

        await db.commit()

        # Re-fetch with loaded relationships
        loaded_agent = await agent_repository.get_by_id(db, agent.id, load_relationships=True)
        return self._to_agent_response(loaded_agent)  # type: ignore[arg-type]

    async def list_agents(
        self,
        db: AsyncSession,
        organization_id: UUID | None = None,
        domain: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AgentResponse]:
        if organization_id is not None:
            org = await organization_repository.get_by_id(db, organization_id)
            if not org:
                raise NotFoundError(f"Organization with ID '{organization_id}' not found.")

        normalized_status = status.strip().capitalize() if status else None
        agents = await agent_repository.list(
            db=db,
            organization_id=organization_id,
            domain=domain.strip() if domain else None,
            status=normalized_status,
            skip=skip,
            limit=limit,
        )
        return [self._to_agent_response(a) for a in agents]

    async def get_agent(
        self,
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID | None = None,
    ) -> AgentResponse:
        agent = await agent_repository.get_by_id(db, agent_id, load_relationships=True)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        if organization_id is not None and agent.organization_id != organization_id:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        return self._to_agent_response(agent)

    async def update_agent(
        self,
        db: AsyncSession,
        agent_id: UUID,
        schema: AgentUpdate,
        organization_id: UUID | None = None,
    ) -> AgentResponse:
        agent = await agent_repository.get_by_id(db, agent_id, load_relationships=True)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        if organization_id is not None and agent.organization_id != organization_id:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        await agent_repository.update(
            db=db,
            agent=agent,
            name=schema.name,
            description=schema.description,
            domain=schema.domain,
            status=schema.status,
            system_instructions=schema.system_instructions,
            require_approval=schema.require_approval,
            touch_updated_at=True,
        )
        await db.commit()

        # Re-fetch with loaded relationships
        loaded = await agent_repository.get_by_id(db, agent.id, load_relationships=True)
        return self._to_agent_response(loaded)  # type: ignore[arg-type]

    async def delete_agent(
        self,
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID | None = None,
    ) -> None:
        agent = await agent_repository.get_by_id(db, agent_id, load_relationships=False)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        if organization_id is not None and agent.organization_id != organization_id:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        await agent_repository.delete(db, agent)
        await db.commit()

    # ==========================================
    # Knowledge Source Relationships
    # ==========================================

    async def list_agent_knowledge_sources(
        self,
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID | None = None,
    ) -> List[KnowledgeSourceResponse]:
        agent = await agent_repository.get_by_id(db, agent_id, load_relationships=False)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        if organization_id is not None and agent.organization_id != organization_id:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        sources = await agent_repository.list_knowledge_sources(db, agent_id)
        responses: List[KnowledgeSourceResponse] = []
        for s in sources:
            doc_count = await knowledge_source_repository.count_documents(db, s.id)
            responses.append(
                KnowledgeSourceResponse(
                    id=s.id,
                    organization_id=s.organization_id,
                    name=s.name,
                    description=s.description,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    document_count=doc_count,
                )
            )
        return responses

    async def attach_knowledge_source(
        self,
        db: AsyncSession,
        agent_id: UUID,
        source_id: UUID,
        organization_id: UUID | None = None,
    ) -> KnowledgeSourceResponse:
        agent = await agent_repository.get_by_id(db, agent_id, load_relationships=False)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        if organization_id is not None and agent.organization_id != organization_id:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        ks = await knowledge_source_repository.get_by_id(db, source_id)
        if not ks or ks.organization_id != agent.organization_id:
            raise NotFoundError(f"Knowledge Source with ID '{source_id}' not found.")

        await agent_repository.add_knowledge_source(db, agent_id, source_id)
        await db.commit()

        doc_count = await knowledge_source_repository.count_documents(db, ks.id)
        return KnowledgeSourceResponse(
            id=ks.id,
            organization_id=ks.organization_id,
            name=ks.name,
            description=ks.description,
            created_at=ks.created_at,
            updated_at=ks.updated_at,
            document_count=doc_count,
        )

    async def detach_knowledge_source(
        self,
        db: AsyncSession,
        agent_id: UUID,
        source_id: UUID,
        organization_id: UUID | None = None,
    ) -> None:
        agent = await agent_repository.get_by_id(db, agent_id, load_relationships=False)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        if organization_id is not None and agent.organization_id != organization_id:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        removed = await agent_repository.remove_knowledge_source(db, agent_id, source_id)
        if not removed:
            raise NotFoundError(
                f"Knowledge Source with ID '{source_id}' is not attached to agent '{agent_id}'."
            )
        await db.commit()

    # ==========================================
    # Tool Relationships
    # ==========================================

    async def list_agent_tools(
        self,
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID | None = None,
    ) -> List[str]:
        agent = await agent_repository.get_by_id(db, agent_id, load_relationships=False)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        if organization_id is not None and agent.organization_id != organization_id:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        tools = await agent_repository.list_tools(db, agent_id)
        return [t.tool_name for t in tools]

    async def attach_tool(
        self,
        db: AsyncSession,
        agent_id: UUID,
        tool_name: str,
        organization_id: UUID | None = None,
    ) -> str:
        agent = await agent_repository.get_by_id(db, agent_id, load_relationships=False)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        if organization_id is not None and agent.organization_id != organization_id:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        cleaned = tool_name.strip()
        if not cleaned:
            raise BadRequestError("Tool name cannot be empty or whitespace.")
        if len(cleaned) > 100:
            raise BadRequestError(f"Tool name '{cleaned}' exceeds maximum length of 100 characters.")

        tool = await agent_repository.add_tool(db, agent_id, cleaned)
        await db.commit()
        return tool.tool_name

    async def detach_tool(
        self,
        db: AsyncSession,
        agent_id: UUID,
        tool_name: str,
        organization_id: UUID | None = None,
    ) -> None:
        agent = await agent_repository.get_by_id(db, agent_id, load_relationships=False)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        if organization_id is not None and agent.organization_id != organization_id:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        cleaned = tool_name.strip()
        removed = await agent_repository.remove_tool(db, agent_id, cleaned)
        if not removed:
            raise NotFoundError(f"Tool '{cleaned}' is not attached to agent '{agent_id}'.")
        await db.commit()


agent_service = AgentService()

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent import Agent, AgentKnowledgeSource, AgentTool
from app.models.knowledge import KnowledgeSource


class AgentRepository:
    """Encapsulates database queries for Agent entities and their relationship mappings."""

    async def create(
        self,
        db: AsyncSession,
        organization_id: UUID,
        created_by_user_id: UUID,
        name: str,
        description: str,
        domain: str,
        status: str = "Active",
        system_instructions: str = "",
        require_approval: bool = False,
    ) -> Agent:
        agent = Agent(
            organization_id=organization_id,
            created_by_user_id=created_by_user_id,
            name=name,
            description=description,
            domain=domain,
            status=status,
            system_instructions=system_instructions,
            require_approval=require_approval,
        )
        db.add(agent)
        await db.flush()
        return agent

    async def list(
        self,
        db: AsyncSession,
        organization_id: UUID | None = None,
        domain: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Agent]:
        stmt = (
            select(Agent)
            .options(
                selectinload(Agent.tools),
                selectinload(Agent.knowledge_sources),
                selectinload(Agent.creator),
            )
            .order_by(Agent.created_at.desc())
        )

        if organization_id is not None:
            stmt = stmt.where(Agent.organization_id == organization_id)
        if domain is not None:
            stmt = stmt.where(Agent.domain == domain)
        if status is not None:
            stmt = stmt.where(Agent.status == status)

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(
        self,
        db: AsyncSession,
        agent_id: UUID,
        load_relationships: bool = True,
    ) -> Agent | None:
        stmt = select(Agent).where(Agent.id == agent_id)
        if load_relationships:
            stmt = stmt.options(
                selectinload(Agent.tools),
                selectinload(Agent.knowledge_sources),
                selectinload(Agent.creator),
            )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        agent: Agent,
        name: str | None = None,
        description: str | None = None,
        domain: str | None = None,
        status: str | None = None,
        system_instructions: str | None = None,
        require_approval: bool | None = None,
        touch_updated_at: bool = False,
    ) -> Agent:
        if name is not None:
            agent.name = name
        if description is not None:
            agent.description = description
        if domain is not None:
            agent.domain = domain
        if status is not None:
            agent.status = status
        if system_instructions is not None:
            agent.system_instructions = system_instructions
        if require_approval is not None:
            agent.require_approval = require_approval
        if touch_updated_at:
            agent.updated_at = datetime.now(timezone.utc)

        await db.flush()
        return agent

    async def delete(self, db: AsyncSession, agent: Agent) -> None:
        await db.delete(agent)
        await db.flush()

    # ==========================================
    # Tool Relationship Operations
    # ==========================================

    async def add_tool(
        self,
        db: AsyncSession,
        agent_id: UUID,
        tool_name: str,
    ) -> AgentTool:
        stmt = select(AgentTool).where(
            AgentTool.agent_id == agent_id,
            AgentTool.tool_name == tool_name,
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        tool = AgentTool(agent_id=agent_id, tool_name=tool_name)
        db.add(tool)
        await db.flush()
        return tool

    async def remove_tool(
        self,
        db: AsyncSession,
        agent_id: UUID,
        tool_name: str,
    ) -> bool:
        stmt = select(AgentTool).where(
            AgentTool.agent_id == agent_id,
            AgentTool.tool_name == tool_name,
        )
        res = await db.execute(stmt)
        tool = res.scalar_one_or_none()
        if tool:
            await db.delete(tool)
            await db.flush()
            return True
        return False

    async def list_tools(
        self,
        db: AsyncSession,
        agent_id: UUID,
    ) -> Sequence[AgentTool]:
        stmt = (
            select(AgentTool)
            .where(AgentTool.agent_id == agent_id)
            .order_by(AgentTool.tool_name.asc())
        )
        res = await db.execute(stmt)
        return res.scalars().all()

    # ==========================================
    # Knowledge Source Relationship Operations
    # ==========================================

    async def add_knowledge_source(
        self,
        db: AsyncSession,
        agent_id: UUID,
        source_id: UUID,
    ) -> AgentKnowledgeSource:
        stmt = select(AgentKnowledgeSource).where(
            AgentKnowledgeSource.agent_id == agent_id,
            AgentKnowledgeSource.source_id == source_id,
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        aks = AgentKnowledgeSource(agent_id=agent_id, source_id=source_id)
        db.add(aks)
        await db.flush()
        return aks

    async def remove_knowledge_source(
        self,
        db: AsyncSession,
        agent_id: UUID,
        source_id: UUID,
    ) -> bool:
        stmt = select(AgentKnowledgeSource).where(
            AgentKnowledgeSource.agent_id == agent_id,
            AgentKnowledgeSource.source_id == source_id,
        )
        res = await db.execute(stmt)
        aks = res.scalar_one_or_none()
        if aks:
            await db.delete(aks)
            await db.flush()
            return True
        return False

    async def list_knowledge_sources(
        self,
        db: AsyncSession,
        agent_id: UUID,
    ) -> Sequence[KnowledgeSource]:
        stmt = (
            select(KnowledgeSource)
            .join(
                AgentKnowledgeSource,
                AgentKnowledgeSource.source_id == KnowledgeSource.id,
            )
            .where(AgentKnowledgeSource.agent_id == agent_id)
            .order_by(KnowledgeSource.name.asc())
        )
        res = await db.execute(stmt)
        return res.scalars().all()


agent_repository = AgentRepository()

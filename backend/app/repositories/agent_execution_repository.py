from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_execution import AgentExecution


class AgentExecutionRepository:
    """Encapsulates database access for AgentExecution entities."""

    async def create(
        self,
        db: AsyncSession,
        organization_id: UUID,
        agent_id: UUID,
        triggered_by_user_id: UUID | None,
        source: str,
        source_reference_id: UUID | None,
        input_prompt: str,
        status: str,
        require_approval: bool,
    ) -> AgentExecution:
        execution = AgentExecution(
            organization_id=organization_id,
            agent_id=agent_id,
            triggered_by_user_id=triggered_by_user_id,
            source=source,
            source_reference_id=source_reference_id,
            input_prompt=input_prompt,
            status=status,
            require_approval=require_approval,
            started_at=datetime.now(timezone.utc),
        )
        db.add(execution)
        await db.flush()
        return execution

    async def get_by_id(
        self,
        db: AsyncSession,
        execution_id: UUID,
    ) -> AgentExecution | None:
        stmt = select(AgentExecution).where(AgentExecution.id == execution_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_agent(
        self,
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AgentExecution]:
        stmt = select(AgentExecution).where(AgentExecution.agent_id == agent_id)
        if organization_id is not None:
            stmt = stmt.where(AgentExecution.organization_id == organization_id)
        if status is not None:
            stmt = stmt.where(AgentExecution.status == status)

        stmt = stmt.order_by(AgentExecution.started_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def list_by_organization(
        self,
        db: AsyncSession,
        organization_id: UUID,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AgentExecution]:
        stmt = select(AgentExecution).where(AgentExecution.organization_id == organization_id)
        if status is not None:
            stmt = stmt.where(AgentExecution.status == status)

        stmt = stmt.order_by(AgentExecution.started_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update_status(
        self,
        db: AsyncSession,
        execution: AgentExecution,
        status: str,
        error_message: str | None = None,
        tokens_used: int | None = None,
        latency_ms: int | None = None,
        completed_at: datetime | None = None,
    ) -> AgentExecution:
        execution.status = status
        if error_message is not None:
            execution.error_message = error_message
        if tokens_used is not None:
            execution.tokens_used = tokens_used
        if latency_ms is not None:
            execution.latency_ms = latency_ms
        if completed_at is not None:
            execution.completed_at = completed_at
        execution.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return execution


    async def update_result(
        self,
        db: AsyncSession,
        execution: AgentExecution,
        output_result: str,
        tokens_used: int = 0,
        latency_ms: int = 0,
        completed_at: datetime | None = None,
    ) -> AgentExecution:
        execution.output_result = output_result
        execution.tokens_used = tokens_used
        execution.latency_ms = latency_ms
        if completed_at is not None:
            execution.completed_at = completed_at
        execution.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return execution

    async def update_approval(
        self,
        db: AsyncSession,
        execution: AgentExecution,
        approved_by_user_id: UUID,
        status: str = "running",
    ) -> AgentExecution:
        execution.approved_by_user_id = approved_by_user_id
        execution.status = status
        execution.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return execution

    async def delete(self, db: AsyncSession, execution: AgentExecution) -> None:
        await db.delete(execution)
        await db.flush()


agent_execution_repository = AgentExecutionRepository()

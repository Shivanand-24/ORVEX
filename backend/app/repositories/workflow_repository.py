from typing import List, Optional, Sequence
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workflow import Workflow, WorkflowStep, WorkflowExecution


class WorkflowRepository:
    """Data access repository for Workflows, Steps, and Workflow Executions."""

    async def get_by_id(
        self,
        db: AsyncSession,
        workflow_id: UUID,
        with_relations: bool = True,
        for_update: bool = False,
    ) -> Optional[Workflow]:
        """Retrieves a single Workflow by its primary key UUID."""
        stmt = select(Workflow).where(Workflow.id == workflow_id)
        if with_relations:
            stmt = stmt.options(
                selectinload(Workflow.steps),
                selectinload(Workflow.executions),
            )
        if for_update:
            stmt = stmt.with_for_update()

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_org(
        self,
        db: AsyncSession,
        organization_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Workflow]:
        """Lists workflows belonging to a specific organization with pagination and status filter."""
        stmt = (
            select(Workflow)
            .where(Workflow.organization_id == organization_id)
            .options(
                selectinload(Workflow.steps),
                selectinload(Workflow.executions),
            )
        )
        if status:
            stmt = stmt.where(Workflow.status == status)

        stmt = stmt.order_by(Workflow.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, workflow: Workflow) -> Workflow:
        """Persists a new Workflow and flushes to the database session."""
        db.add(workflow)
        await db.flush()
        return workflow

    async def update(self, db: AsyncSession, workflow: Workflow) -> Workflow:
        """Flushes in-memory modifications on a Workflow to the session."""
        workflow.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return workflow

    async def delete(self, db: AsyncSession, workflow: Workflow) -> None:
        """Deletes a Workflow; cascade="all, delete-orphan" cleans up steps and executions."""
        await db.delete(workflow)
        await db.flush()

    async def replace_steps(
        self,
        db: AsyncSession,
        workflow: Workflow,
        new_steps: List[WorkflowStep],
    ) -> List[WorkflowStep]:
        """Atomically replaces a workflow's steps graph."""
        workflow.steps = new_steps
        workflow.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return workflow.steps

    # ==========================================
    # Workflow Execution Methods
    # ==========================================

    async def create_execution(
        self,
        db: AsyncSession,
        execution: WorkflowExecution,
    ) -> WorkflowExecution:
        """Persists a new WorkflowExecution row."""
        db.add(execution)
        await db.flush()
        return execution

    async def get_execution_by_id(
        self,
        db: AsyncSession,
        execution_id: UUID,
        for_update: bool = False,
    ) -> Optional[WorkflowExecution]:
        """Retrieves a WorkflowExecution, optionally acquiring a row-level lock."""
        stmt = (
            select(WorkflowExecution)
            .where(WorkflowExecution.id == execution_id)
            .options(selectinload(WorkflowExecution.workflow))
        )
        if for_update:
            stmt = stmt.with_for_update()

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_executions_by_workflow(
        self,
        db: AsyncSession,
        workflow_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[WorkflowExecution]:
        """Lists chronological executions for a workflow."""
        stmt = (
            select(WorkflowExecution)
            .where(WorkflowExecution.workflow_id == workflow_id)
            .order_by(WorkflowExecution.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update_execution(
        self,
        db: AsyncSession,
        execution: WorkflowExecution,
    ) -> WorkflowExecution:
        """Flushes updates to a WorkflowExecution."""
        await db.flush()
        return execution


workflow_repository = WorkflowRepository()

from datetime import datetime, timezone
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, NotFoundError
from app.execution.approval import approval_manager
from app.execution.lifecycle import ExecutionStatus, validate_transition
from app.execution.resolver import agent_resolver
from app.models.agent_execution import AgentExecution
from app.models.audit import AuditLog
from app.repositories.agent_execution_repository import agent_execution_repository
from app.repositories.agent_repository import agent_repository
from app.repositories.membership_repository import membership_repository
from app.repositories.organization_repository import organization_repository
from app.repositories.user_repository import user_repository
from app.schemas.agent_execution import (
    AgentExecutionCreate,
    AgentExecutionResponse,
    ApprovalRequest,
    CancellationRequest,
)


class AgentExecutionService:
    """Orchestrates Agent Execution lifecycle, validation, approval, and audit logging."""

    @staticmethod
    def _to_response(execution: AgentExecution) -> AgentExecutionResponse:
        return AgentExecutionResponse(
            id=execution.id,
            organization_id=execution.organization_id,
            agent_id=execution.agent_id,
            triggered_by_user_id=execution.triggered_by_user_id,
            source=execution.source,
            source_reference_id=execution.source_reference_id,
            input_prompt=execution.input_prompt,
            status=execution.status,
            require_approval=execution.require_approval,
            approved_by_user_id=execution.approved_by_user_id,
            output_result=execution.output_result,
            error_message=execution.error_message,
            tokens_used=execution.tokens_used,
            latency_ms=execution.latency_ms,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            created_at=execution.created_at,
            updated_at=execution.updated_at,
        )

    async def _emit_audit_event(
        self,
        db: AsyncSession,
        organization_id: UUID,
        actor_id: UUID | None,
        action: str,
        execution_id: UUID,
        details: dict,
    ) -> None:
        """Helper to record sanitized metadata-only audit logs."""
        audit_log = AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
            resource_type="agent_execution",
            resource_id=execution_id,
            details=details,
        )
        db.add(audit_log)
        await db.flush()

    async def create_execution(
        self,
        db: AsyncSession,
        agent_id: UUID,
        schema: AgentExecutionCreate,
    ) -> AgentExecutionResponse:
        # Validate organization exists
        org = await organization_repository.get_by_id(db, schema.organization_id)
        if not org:
            raise NotFoundError(f"Organization with ID '{schema.organization_id}' not found.")

        # Resolve and validate active agent with tenant isolation
        agent = await agent_resolver.resolve_for_execution(
            db, agent_id=agent_id, organization_id=schema.organization_id
        )

        # Validate triggered_by_user_id if provided
        triggered_by = schema.triggered_by_user_id
        if triggered_by is not None:
            user = await user_repository.get_by_id(db, triggered_by)
            if not user:
                raise NotFoundError(f"User with ID '{triggered_by}' not found.")

            # Validate membership in organization
            membership = await membership_repository.find_by_organization_and_user(
                db, organization_id=schema.organization_id, user_id=triggered_by
            )
            if not membership:
                raise BadRequestError(
                    f"User '{triggered_by}' is not a member of organization '{schema.organization_id}'."
                )

        # Evaluate approval requirement from existing agent model
        require_approval = approval_manager.should_require_approval(agent)
        initial_status = (
            ExecutionStatus.WAITING_FOR_APPROVAL.value
            if require_approval
            else ExecutionStatus.RUNNING.value
        )

        # Create persistent database record
        execution = await agent_execution_repository.create(
            db=db,
            organization_id=schema.organization_id,
            agent_id=agent.id,
            triggered_by_user_id=triggered_by,
            source=schema.source,
            source_reference_id=schema.source_reference_id,
            input_prompt=schema.input_prompt,
            status=initial_status,
            require_approval=require_approval,
        )

        # Emit audit: agent.execution.created
        await self._emit_audit_event(
            db=db,
            organization_id=execution.organization_id,
            actor_id=triggered_by,
            action="agent.execution.created",
            execution_id=execution.id,
            details={
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "domain": agent.domain,
                "source": schema.source,
                "prompt_length": len(schema.input_prompt),
                "require_approval": require_approval,
                "initial_status": initial_status,
            },
        )

        # Emit audit: approval_requested or started
        if require_approval:
            await self._emit_audit_event(
                db=db,
                organization_id=execution.organization_id,
                actor_id=triggered_by,
                action="agent.execution.approval_requested",
                execution_id=execution.id,
                details={
                    "agent_id": str(agent.id),
                    "status": "waiting_for_approval",
                },
            )
        else:
            await self._emit_audit_event(
                db=db,
                organization_id=execution.organization_id,
                actor_id=triggered_by,
                action="agent.execution.started",
                execution_id=execution.id,
                details={
                    "agent_id": str(agent.id),
                    "status": "running",
                },
            )

        await db.commit()
        await db.refresh(execution)
        return self._to_response(execution)

    async def get_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        organization_id: UUID | None = None,
    ) -> AgentExecutionResponse:
        execution = await agent_execution_repository.get_by_id(db, execution_id)
        if not execution:
            raise NotFoundError(f"Agent execution with ID '{execution_id}' not found.")

        # Enforce multi-tenant isolation (404 masking)
        if organization_id is not None and execution.organization_id != organization_id:
            raise NotFoundError(f"Agent execution with ID '{execution_id}' not found.")

        return self._to_response(execution)

    async def list_executions_by_agent(
        self,
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AgentExecutionResponse]:
        # Validate agent exists and matches tenant
        agent = await agent_repository.get_by_id(db, agent_id, load_relationships=False)
        if not agent:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        if organization_id is not None and agent.organization_id != organization_id:
            raise NotFoundError(f"Agent with ID '{agent_id}' not found.")

        normalized_status = status.strip().lower() if status else None
        executions = await agent_execution_repository.list_by_agent(
            db=db,
            agent_id=agent_id,
            organization_id=organization_id,
            status=normalized_status,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(e) for e in executions]

    async def approve_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        payload: ApprovalRequest,
        organization_id: UUID | None = None,
    ) -> AgentExecutionResponse:
        execution = await agent_execution_repository.get_by_id(db, execution_id)
        if not execution:
            raise NotFoundError(f"Agent execution with ID '{execution_id}' not found.")

        if organization_id is not None and execution.organization_id != organization_id:
            raise NotFoundError(f"Agent execution with ID '{execution_id}' not found.")

        # Validate that current status allows transition to RUNNING
        validate_transition(execution.status, ExecutionStatus.RUNNING)

        # Validate approver belongs to the tenant organization
        await approval_manager.validate_approver(
            db, organization_id=execution.organization_id, approver_user_id=payload.user_id
        )

        # Update execution approval and transition to RUNNING
        updated = await agent_execution_repository.update_approval(
            db=db,
            execution=execution,
            approved_by_user_id=payload.user_id,
            status=ExecutionStatus.RUNNING.value,
        )

        # Emit audit: agent.execution.approved
        await self._emit_audit_event(
            db=db,
            organization_id=execution.organization_id,
            actor_id=payload.user_id,
            action="agent.execution.approved",
            execution_id=execution.id,
            details={
                "agent_id": str(execution.agent_id),
                "approver_user_id": str(payload.user_id),
                "status": "running",
            },
        )

        # Emit audit: agent.execution.started
        await self._emit_audit_event(
            db=db,
            organization_id=execution.organization_id,
            actor_id=execution.triggered_by_user_id,
            action="agent.execution.started",
            execution_id=execution.id,
            details={
                "agent_id": str(execution.agent_id),
                "status": "running",
            },
        )

        await db.commit()
        await db.refresh(updated)
        return self._to_response(updated)

    async def cancel_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        payload: CancellationRequest,
        organization_id: UUID | None = None,
    ) -> AgentExecutionResponse:
        execution = await agent_execution_repository.get_by_id(db, execution_id)
        if not execution:
            raise NotFoundError(f"Agent execution with ID '{execution_id}' not found.")

        if organization_id is not None and execution.organization_id != organization_id:
            raise NotFoundError(f"Agent execution with ID '{execution_id}' not found.")

        previous_status = execution.status
        validate_transition(previous_status, ExecutionStatus.CANCELLED)

        # If user_id provided, validate membership
        if payload.user_id is not None:
            await approval_manager.validate_approver(
                db, organization_id=execution.organization_id, approver_user_id=payload.user_id
            )

        reason = payload.reason.strip() if payload.reason else "Cancelled by user"
        updated = await agent_execution_repository.update_status(
            db=db,
            execution=execution,
            status=ExecutionStatus.CANCELLED.value,
            error_message=reason,
            completed_at=datetime.now(timezone.utc),
        )

        # If previous status was waiting_for_approval, this is an approval rejection
        audit_action = (
            "agent.execution.rejected"
            if previous_status == ExecutionStatus.WAITING_FOR_APPROVAL.value
            else "agent.execution.cancelled"
        )

        await self._emit_audit_event(
            db=db,
            organization_id=execution.organization_id,
            actor_id=payload.user_id,
            action=audit_action,
            execution_id=execution.id,
            details={
                "agent_id": str(execution.agent_id),
                "previous_status": previous_status,
                "status": "cancelled",
                "reason": reason,
            },
        )

        await db.commit()
        await db.refresh(updated)
        return self._to_response(updated)

    async def complete_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        output_result: str,
        tokens_used: int = 0,
        latency_ms: int = 0,
        organization_id: UUID | None = None,
    ) -> AgentExecutionResponse:
        """Completes an active execution run."""
        execution = await agent_execution_repository.get_by_id(db, execution_id)
        if not execution:
            raise NotFoundError(f"Agent execution with ID '{execution_id}' not found.")

        if organization_id is not None and execution.organization_id != organization_id:
            raise NotFoundError(f"Agent execution with ID '{execution_id}' not found.")

        validate_transition(execution.status, ExecutionStatus.COMPLETED)

        updated = await agent_execution_repository.update_result(
            db=db,
            execution=execution,
            output_result=output_result,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            completed_at=datetime.now(timezone.utc),
        )
        updated.status = ExecutionStatus.COMPLETED.value

        await self._emit_audit_event(
            db=db,
            organization_id=execution.organization_id,
            actor_id=execution.triggered_by_user_id,
            action="agent.execution.completed",
            execution_id=execution.id,
            details={
                "agent_id": str(execution.agent_id),
                "status": "completed",
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
                "output_length": len(output_result),
            },
        )

        await db.commit()
        await db.refresh(updated)
        return self._to_response(updated)

    async def fail_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        error_message: str,
        tokens_used: int = 0,
        latency_ms: int = 0,
        organization_id: UUID | None = None,
    ) -> AgentExecutionResponse:
        """Fails an active execution run."""
        execution = await agent_execution_repository.get_by_id(db, execution_id)
        if not execution:
            raise NotFoundError(f"Agent execution with ID '{execution_id}' not found.")

        if organization_id is not None and execution.organization_id != organization_id:
            raise NotFoundError(f"Agent execution with ID '{execution_id}' not found.")

        validate_transition(execution.status, ExecutionStatus.FAILED)

        updated = await agent_execution_repository.update_status(
            db=db,
            execution=execution,
            status=ExecutionStatus.FAILED.value,
            error_message=error_message,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            completed_at=datetime.now(timezone.utc),
        )

        await self._emit_audit_event(
            db=db,
            organization_id=execution.organization_id,
            actor_id=execution.triggered_by_user_id,
            action="agent.execution.failed",
            execution_id=execution.id,
            details={
                "agent_id": str(execution.agent_id),
                "status": "failed",
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
                "error_message": error_message,
            },
        )

        await db.commit()
        await db.refresh(updated)
        return self._to_response(updated)


agent_execution_service = AgentExecutionService()

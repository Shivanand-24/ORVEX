import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, NotFoundError
from app.models.audit import AuditLog
from app.models.workflow import Workflow, WorkflowStep, WorkflowExecution
from app.repositories.agent_repository import agent_repository
from app.repositories.knowledge_source_repository import knowledge_source_repository
from app.repositories.membership_repository import membership_repository
from app.repositories.organization_repository import organization_repository
from app.repositories.user_repository import user_repository
from app.repositories.workflow_repository import workflow_repository
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowStepCreate,
    WorkflowStepResponse,
    WorkflowExecutionResponse,
    WorkflowApprovalRequest,
    WorkflowCancellationRequest,
)
from app.workflows.adapters import (
    default_agent_adapter,
    default_knowledge_adapter,
    default_action_adapter,
    default_condition_adapter,
)
from app.workflows.dag import graph_validator, MAX_EXECUTION_STEPS


class WorkflowService:
    """Business logic and orchestration service for Workflows, Step Graphs, and Executions."""

    # ==========================================
    # Workflow CRUD Operations
    # ==========================================

    async def create_workflow(
        self,
        db: AsyncSession,
        schema: WorkflowCreate,
    ) -> WorkflowResponse:
        """Creates a new Workflow with an optional validated initial steps graph."""
        # 1. Validate organization exists
        org = await organization_repository.get_by_id(db, schema.organization_id)
        if not org:
            raise NotFoundError(f"Organization '{schema.organization_id}' not found.")

        # 2. Resolve creator user
        creator_id = await self._resolve_creator_user(
            db=db,
            organization_id=schema.organization_id,
            requested_user_id=schema.created_by_user_id,
        )

        # 3. Handle trigger alias
        trigger_type = schema.trigger_type or schema.trigger or "Manual"

        # 4. Prepare and validate initial steps graph if provided
        initial_steps: List[WorkflowStep] = []
        if schema.steps:
            temp_steps_data = self._normalize_step_items(schema.steps)

            # Validate DAG properties
            graph_validator.validate_graph(temp_steps_data)

            # Validate cross-tenant references in step configs
            await self._validate_step_configs_tenant(
                db=db,
                organization_id=schema.organization_id,
                steps=schema.steps,
            )

            for s_data in temp_steps_data:
                initial_steps.append(
                    WorkflowStep(
                        id=s_data["id"],
                        step_order=s_data["step_order"],
                        type=s_data["type"],
                        title=s_data["title"],
                        description=s_data["description"],
                        config=s_data["config"],
                        next_step_ids=s_data["next_step_ids"],
                    )
                )

        workflow = Workflow(
            id=uuid.uuid4(),
            organization_id=schema.organization_id,
            created_by_user_id=creator_id,
            name=schema.name,
            description=schema.description,
            status=schema.status,
            trigger_type=trigger_type,
            steps=initial_steps,
        )

        created = await workflow_repository.create(db, workflow)

        # Emit audit: workflow.created
        await self._emit_audit_event(
            db=db,
            organization_id=workflow.organization_id,
            actor_id=creator_id,
            action="workflow.created",
            workflow_id=workflow.id,
            details={
                "name": workflow.name,
                "status": workflow.status,
                "trigger_type": workflow.trigger_type,
                "step_count": len(initial_steps),
            },
        )

        await db.commit()
        refetched = await workflow_repository.get_by_id(db, created.id)
        return self._to_response(refetched)

    async def list_workflows(
        self,
        db: AsyncSession,
        organization_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WorkflowResponse]:
        """Lists workflows for an organization with pagination and computed metrics."""
        org = await organization_repository.get_by_id(db, organization_id)
        if not org:
            raise NotFoundError(f"Organization '{organization_id}' not found.")

        workflows = await workflow_repository.list_by_org(
            db=db,
            organization_id=organization_id,
            status=status,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(w) for w in workflows]

    async def get_workflow(
        self,
        db: AsyncSession,
        workflow_id: UUID,
        organization_id: Optional[UUID] = None,
    ) -> WorkflowResponse:
        """Retrieves a single workflow with full steps graph and execution metrics."""
        workflow = await workflow_repository.get_by_id(db, workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        if organization_id is not None and workflow.organization_id != organization_id:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        return self._to_response(workflow)

    async def update_workflow(
        self,
        db: AsyncSession,
        workflow_id: UUID,
        schema: WorkflowUpdate,
        organization_id: Optional[UUID] = None,
    ) -> WorkflowResponse:
        """Updates workflow metadata (name, description, status, trigger)."""
        workflow = await workflow_repository.get_by_id(db, workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        if organization_id is not None and workflow.organization_id != organization_id:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        if schema.name is not None:
            workflow.name = schema.name
        if schema.description is not None:
            workflow.description = schema.description
        if schema.status is not None:
            workflow.status = schema.status
        if schema.trigger_type is not None:
            workflow.trigger_type = schema.trigger_type
        elif schema.trigger is not None:
            workflow.trigger_type = schema.trigger

        updated = await workflow_repository.update(db, workflow)

        await self._emit_audit_event(
            db=db,
            organization_id=workflow.organization_id,
            actor_id=workflow.created_by_user_id,
            action="workflow.updated",
            workflow_id=workflow.id,
            details={
                "name": workflow.name,
                "status": workflow.status,
                "trigger_type": workflow.trigger_type,
            },
        )

        await db.commit()
        refetched = await workflow_repository.get_by_id(db, updated.id)
        return self._to_response(refetched)

    async def toggle_status(
        self,
        db: AsyncSession,
        workflow_id: UUID,
        organization_id: Optional[UUID] = None,
    ) -> WorkflowResponse:
        """Toggles workflow status between Active and Paused (or Draft -> Active)."""
        workflow = await workflow_repository.get_by_id(db, workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        if organization_id is not None and workflow.organization_id != organization_id:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        new_status = "Paused" if workflow.status == "Active" else "Active"
        workflow.status = new_status
        updated = await workflow_repository.update(db, workflow)

        await self._emit_audit_event(
            db=db,
            organization_id=workflow.organization_id,
            actor_id=workflow.created_by_user_id,
            action="workflow.status_toggled",
            workflow_id=workflow.id,
            details={"previous_status": workflow.status, "new_status": new_status},
        )

        await db.commit()
        refetched = await workflow_repository.get_by_id(db, updated.id)
        return self._to_response(refetched)

    async def delete_workflow(
        self,
        db: AsyncSession,
        workflow_id: UUID,
        organization_id: Optional[UUID] = None,
    ) -> None:
        """Deletes a workflow and all associated steps and execution history."""
        workflow = await workflow_repository.get_by_id(db, workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        if organization_id is not None and workflow.organization_id != organization_id:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        await workflow_repository.delete(db, workflow)

        await self._emit_audit_event(
            db=db,
            organization_id=workflow.organization_id,
            actor_id=workflow.created_by_user_id,
            action="workflow.deleted",
            workflow_id=workflow.id,
            details={"name": workflow.name},
        )

        await db.commit()

    async def replace_steps(
        self,
        db: AsyncSession,
        workflow_id: UUID,
        steps: List[WorkflowStepCreate],
        organization_id: Optional[UUID] = None,
    ) -> WorkflowResponse:
        """Atomically replaces the step graph for a workflow after DAG validation."""
        workflow = await workflow_repository.get_by_id(db, workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        if organization_id is not None and workflow.organization_id != organization_id:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        # Prepare normalized step items with deterministic UUIDs
        step_items_data = self._normalize_step_items(steps)

        # Validate DAG rules
        graph_validator.validate_graph(step_items_data)

        # Validate cross-tenant step references
        await self._validate_step_configs_tenant(
            db=db,
            organization_id=workflow.organization_id,
            steps=steps,
        )

        new_step_entities = [
            WorkflowStep(
                id=s_data["id"],
                workflow_id=workflow.id,
                step_order=s_data["step_order"],
                type=s_data["type"],
                title=s_data["title"],
                description=s_data["description"],
                config=s_data["config"],
                next_step_ids=s_data["next_step_ids"],
            )
            for s_data in step_items_data
        ]

        await workflow_repository.replace_steps(db, workflow, new_step_entities)

        await self._emit_audit_event(
            db=db,
            organization_id=workflow.organization_id,
            actor_id=workflow.created_by_user_id,
            action="workflow.steps_updated",
            workflow_id=workflow.id,
            details={"step_count": len(new_step_entities)},
        )

        await db.commit()
        refetched = await workflow_repository.get_by_id(db, workflow.id)
        return self._to_response(refetched)

    # ==========================================
    # Workflow Orchestration & Execution Engine
    # ==========================================

    async def execute_workflow(
        self,
        db: AsyncSession,
        workflow_id: UUID,
        triggered_by_user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
    ) -> WorkflowExecutionResponse:
        """Triggers execution of an active workflow."""
        workflow = await workflow_repository.get_by_id(db, workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        if organization_id is not None and workflow.organization_id != organization_id:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        # Workflow must be Active to execute
        if workflow.status != "Active":
            raise BadRequestError(
                f"Cannot execute workflow '{workflow.name}': status is '{workflow.status}', but must be 'Active'."
            )

        if not workflow.steps:
            raise BadRequestError(
                f"Cannot execute workflow '{workflow.name}': workflow has no configured steps."
            )

        # Validate steps graph before running
        graph_validator.validate_graph(workflow.steps)

        # Initialize execution row
        execution = WorkflowExecution(
            id=uuid.uuid4(),
            workflow_id=workflow.id,
            triggered_by_user_id=triggered_by_user_id,
            status="running",
            started_at=datetime.now(timezone.utc),
            execution_log=[],
        )
        await workflow_repository.create_execution(db, execution)

        await self._emit_audit_event(
            db=db,
            organization_id=workflow.organization_id,
            actor_id=triggered_by_user_id,
            action="workflow.execution.started",
            workflow_id=workflow.id,
            execution_id=execution.id,
            details={"step_count": len(workflow.steps)},
        )

        # Map steps by ID and locate the unique root Trigger step
        step_map: Dict[str, WorkflowStep] = {str(s.id): s for s in workflow.steps}
        root_step = self._find_root_trigger_step(workflow.steps)

        # Run traversal engine
        await self._run_traversal(
            db=db,
            workflow=workflow,
            execution=execution,
            step_map=step_map,
            start_step_id=str(root_step.id),
        )

        await db.commit()
        refetched_exec = await workflow_repository.get_execution_by_id(db, execution.id)
        return self._to_execution_response(refetched_exec)

    async def approve_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        payload: WorkflowApprovalRequest,
        organization_id: Optional[UUID] = None,
    ) -> WorkflowExecutionResponse:
        """Approves a workflow run paused in 'waiting_approval' and resumes traversal."""
        # Row-level lock via with_for_update() prevents concurrent duplicate approval races
        execution = await workflow_repository.get_execution_by_id(db, execution_id, for_update=True)
        if not execution:
            raise NotFoundError(f"Workflow execution '{execution_id}' not found.")

        workflow = await workflow_repository.get_by_id(db, execution.workflow_id, with_relations=True)
        if not workflow:
            raise NotFoundError(f"Workflow '{execution.workflow_id}' not found.")

        if organization_id is not None and workflow.organization_id != organization_id:
            raise NotFoundError(f"Workflow execution '{execution_id}' not found.")

        # Approver must belong to the workflow's owning organization
        membership = await membership_repository.find_by_organization_and_user(
            db, workflow.organization_id, payload.user_id
        )
        if not membership:
            raise BadRequestError("Approver user is not an active member of this organization.")

        # State machine check: must be waiting_approval
        if execution.status != "waiting_approval":
            raise BadRequestError(
                f"Workflow execution '{execution_id}' is in status '{execution.status}', not 'waiting_approval'."
            )

        # Locate the paused approval step entry in the execution log
        paused_log_entry = None
        for entry in execution.execution_log:
            if entry.get("status") == "waiting_approval":
                paused_log_entry = entry
                break

        resume_step_id = paused_log_entry.get("resume_step_id") if paused_log_entry else None

        # Update paused log entry with approval details
        if paused_log_entry:
            paused_log_entry["status"] = "approved"
            paused_log_entry["approved_by_user_id"] = str(payload.user_id)
            paused_log_entry["approved_at"] = datetime.now(timezone.utc).isoformat()

        # Update execution status back to running
        execution.status = "running"
        await workflow_repository.update_execution(db, execution)

        # Emit audit event: workflow.execution.approved
        await self._emit_audit_event(
            db=db,
            organization_id=workflow.organization_id,
            actor_id=payload.user_id,
            action="workflow.execution.approved",
            workflow_id=workflow.id,
            execution_id=execution.id,
            details={"approver_user_id": str(payload.user_id)},
        )

        # If a downstream step was queued, resume traversal from resume_step_id
        if resume_step_id:
            step_map: Dict[str, WorkflowStep] = {str(s.id): s for s in workflow.steps}
            await self._run_traversal(
                db=db,
                workflow=workflow,
                execution=execution,
                step_map=step_map,
                start_step_id=resume_step_id,
            )
        else:
            # Approval step was the terminal step
            execution.status = "completed"
            execution.completed_at = datetime.now(timezone.utc)
            await workflow_repository.update_execution(db, execution)
            await self._emit_audit_event(
                db=db,
                organization_id=workflow.organization_id,
                actor_id=execution.triggered_by_user_id,
                action="workflow.execution.completed",
                workflow_id=workflow.id,
                execution_id=execution.id,
                details={"status": "completed"},
            )

        await db.commit()
        refetched_exec = await workflow_repository.get_execution_by_id(db, execution.id)
        return self._to_execution_response(refetched_exec)

    async def cancel_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        payload: WorkflowCancellationRequest,
        organization_id: Optional[UUID] = None,
    ) -> WorkflowExecutionResponse:
        """Cancels a pending or running workflow execution, or rejects one waiting approval."""
        execution = await workflow_repository.get_execution_by_id(db, execution_id, for_update=True)
        if not execution:
            raise NotFoundError(f"Workflow execution '{execution_id}' not found.")

        workflow = await workflow_repository.get_by_id(db, execution.workflow_id, with_relations=False)
        if not workflow:
            raise NotFoundError(f"Workflow '{execution.workflow_id}' not found.")

        if organization_id is not None and workflow.organization_id != organization_id:
            raise NotFoundError(f"Workflow execution '{execution_id}' not found.")

        if execution.status in ("completed", "failed", "cancelled"):
            raise BadRequestError(
                f"Cannot cancel workflow execution: execution is already in terminal state '{execution.status}'."
            )

        execution.status = "cancelled"
        execution.completed_at = datetime.now(timezone.utc)

        current_log = list(execution.execution_log)
        current_log.append({
            "action": "cancelled",
            "cancelled_by_user_id": str(payload.user_id) if payload.user_id else None,
            "reason": payload.reason or "User requested cancellation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        execution.execution_log = current_log

        await workflow_repository.update_execution(db, execution)

        await self._emit_audit_event(
            db=db,
            organization_id=workflow.organization_id,
            actor_id=payload.user_id or execution.triggered_by_user_id,
            action="workflow.execution.cancelled",
            workflow_id=workflow.id,
            execution_id=execution.id,
            details={"reason": payload.reason or "Cancellation requested"},
        )

        await db.commit()
        refetched_exec = await workflow_repository.get_execution_by_id(db, execution.id)
        return self._to_execution_response(refetched_exec)

    async def list_executions(
        self,
        db: AsyncSession,
        workflow_id: UUID,
        organization_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WorkflowExecutionResponse]:
        """Lists historical execution runs for a specific workflow."""
        workflow = await workflow_repository.get_by_id(db, workflow_id, with_relations=False)
        if not workflow:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        if organization_id is not None and workflow.organization_id != organization_id:
            raise NotFoundError(f"Workflow '{workflow_id}' not found.")

        executions = await workflow_repository.list_executions_by_workflow(
            db=db, workflow_id=workflow_id, skip=skip, limit=limit
        )
        return [self._to_execution_response(e) for e in executions]

    async def get_execution(
        self,
        db: AsyncSession,
        execution_id: UUID,
        organization_id: Optional[UUID] = None,
    ) -> WorkflowExecutionResponse:
        """Retrieves a single execution run with complete step logs."""
        execution = await workflow_repository.get_execution_by_id(db, execution_id)
        if not execution:
            raise NotFoundError(f"Workflow execution '{execution_id}' not found.")

        if organization_id is not None:
            workflow = await workflow_repository.get_by_id(db, execution.workflow_id, with_relations=False)
            if not workflow or workflow.organization_id != organization_id:
                raise NotFoundError(f"Workflow execution '{execution_id}' not found.")

        return self._to_execution_response(execution)

    # ==========================================
    # Internal Traversal & Helper Engine
    # ==========================================

    async def _run_traversal(
        self,
        db: AsyncSession,
        workflow: Workflow,
        execution: WorkflowExecution,
        step_map: Dict[str, WorkflowStep],
        start_step_id: str,
    ) -> None:
        """Traverses the workflow step graph deterministically, updating execution_log."""
        curr_step_id: Optional[str] = start_step_id
        steps_executed = 0
        execution_log = list(execution.execution_log)

        while curr_step_id and steps_executed < MAX_EXECUTION_STEPS:
            step = step_map.get(curr_step_id)
            if not step:
                # Target step not in map
                break

            steps_executed += 1
            step_type = step.type

            # Check if this is a Human Approval step
            if step_type == "Human Approval":
                # Deterministic resume cursor points to the first outgoing edge (if any)
                resume_target = str(step.next_step_ids[0]) if step.next_step_ids else None
                execution.status = "waiting_approval"
                execution_log.append({
                    "step_id": str(step.id),
                    "step_order": step.step_order,
                    "type": step.type,
                    "title": step.title,
                    "status": "waiting_approval",
                    "paused_at": datetime.now(timezone.utc).isoformat(),
                    "approver_role": step.config.get("approverRole"),
                    "resume_step_id": resume_target,
                })
                execution.execution_log = execution_log
                await workflow_repository.update_execution(db, execution)

                await self._emit_audit_event(
                    db=db,
                    organization_id=workflow.organization_id,
                    actor_id=execution.triggered_by_user_id,
                    action="workflow.execution.waiting_approval",
                    workflow_id=workflow.id,
                    execution_id=execution.id,
                    details={"step_id": str(step.id), "step_title": step.title},
                )
                # Halt execution loop; waiting for external approval
                return

            # Execute other step types via adapters
            step_output: Dict[str, Any] = {}
            if step_type == "AI Agent":
                agent_id_raw = step.config.get("agent_id")
                prompt_task = step.config.get("task") or f"Execute agent task for step {step.title}"
                if agent_id_raw:
                    try:
                        agent_uuid = UUID(str(agent_id_raw))
                        step_output = await default_agent_adapter.execute_agent_step(
                            db=db,
                            agent_id=agent_uuid,
                            prompt=prompt_task,
                            organization_id=workflow.organization_id,
                            workflow_execution_id=execution.id,
                            step_id=step.id,
                            triggered_by_user_id=execution.triggered_by_user_id,
                        )
                    except Exception as e:
                        step_output = {"error": str(e), "status": "completed_fallback"}
                else:
                    step_output = {"status": "completed", "output_result": f"Simulated run for {step.title}"}

            elif step_type == "Knowledge Retrieval":
                source_id_raw = step.config.get("source_id") or step.config.get("sourceId")
                if source_id_raw:
                    try:
                        src_uuid = UUID(str(source_id_raw))
                        step_output = await default_knowledge_adapter.execute_retrieval_step(
                            db=db,
                            source_id=src_uuid,
                            query="Workflow query context",
                            organization_id=workflow.organization_id,
                        )
                    except Exception as e:
                        step_output = {"error": str(e), "status": "completed"}
                else:
                    step_output = {"status": "completed", "summary": "Retrieved enterprise knowledge context."}

            elif step_type == "Action":
                action_name = step.config.get("action") or step.title
                step_output = await default_action_adapter.execute_action_step(
                    action_name=action_name,
                    config=step.config,
                    organization_id=workflow.organization_id,
                )

            elif step_type == "Condition":
                condition_expr = step.config.get("condition") or "True"
                eval_result = default_condition_adapter.evaluate_condition(
                    condition_expression=condition_expr,
                    context={"execution_id": str(execution.id)},
                )
                step_output = {"condition": condition_expr, "evaluated": eval_result}
                # Select branch based on condition evaluation
                if step.next_step_ids:
                    if eval_result and len(step.next_step_ids) > 0:
                        curr_step_id = str(step.next_step_ids[0])
                    elif not eval_result and len(step.next_step_ids) > 1:
                        curr_step_id = str(step.next_step_ids[1])
                    else:
                        curr_step_id = str(step.next_step_ids[0])
                else:
                    curr_step_id = None

                execution_log.append({
                    "step_id": str(step.id),
                    "step_order": step.step_order,
                    "type": step.type,
                    "title": step.title,
                    "status": "completed",
                    "output": step_output,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                continue

            elif step_type == "Trigger":
                step_output = {"trigger": step.config.get("trigger", "Manual"), "status": "fired"}

            execution_log.append({
                "step_id": str(step.id),
                "step_order": step.step_order,
                "type": step.type,
                "title": step.title,
                "status": "completed",
                "output": step_output,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Advance to next step (first edge or sequence)
            if step.next_step_ids:
                curr_step_id = str(step.next_step_ids[0])
            else:
                curr_step_id = None

        # Traversal successfully reached terminal step
        execution.status = "completed"
        execution.completed_at = datetime.now(timezone.utc)
        execution.execution_log = execution_log
        await workflow_repository.update_execution(db, execution)

        await self._emit_audit_event(
            db=db,
            organization_id=workflow.organization_id,
            actor_id=execution.triggered_by_user_id,
            action="workflow.execution.completed",
            workflow_id=workflow.id,
            execution_id=execution.id,
            details={"steps_executed": steps_executed},
        )

    def _find_root_trigger_step(self, steps: Sequence[WorkflowStep]) -> WorkflowStep:
        """Finds the unique root Trigger step (in-degree == 0)."""
        target_ids: Set[str] = set()
        for s in steps:
            for nxt in s.next_step_ids:
                target_ids.add(str(nxt))

        roots = [s for s in steps if str(s.id) not in target_ids and s.type == "Trigger"]
        if roots:
            return roots[0]
        # Fallback to step_order == 1 or first step
        sorted_steps = sorted(steps, key=lambda s: s.step_order)
        return sorted_steps[0]

    async def _resolve_creator_user(
        self,
        db: AsyncSession,
        organization_id: UUID,
        requested_user_id: Optional[UUID],
    ) -> UUID:
        """Validates creator user or falls back to an organization member."""
        if requested_user_id is not None:
            user = await user_repository.get_by_id(db, requested_user_id)
            if not user:
                raise NotFoundError(f"User '{requested_user_id}' not found.")
            membership = await membership_repository.find_by_organization_and_user(
                db, organization_id, requested_user_id
            )
            if not membership:
                raise BadRequestError(
                    f"User '{requested_user_id}' is not a member of organization '{organization_id}'."
                )
            return requested_user_id

        # Fallback to first active member
        memberships = await membership_repository.list_by_organization(db, organization_id, skip=0, limit=1)
        if memberships:
            return memberships[0].user_id

        raise BadRequestError(
            f"Cannot create workflow: Organization '{organization_id}' has no members."
        )

    @staticmethod
    def _normalize_step_items(steps: Sequence[WorkflowStepCreate]) -> List[Dict[str, Any]]:
        slug_to_uuid: Dict[str, UUID] = {}
        for s in steps:
            raw_id = s.id
            if raw_id:
                if isinstance(raw_id, UUID):
                    slug_to_uuid[str(raw_id)] = raw_id
                else:
                    s_str = str(raw_id).strip()
                    try:
                        slug_to_uuid[s_str] = UUID(s_str)
                    except ValueError:
                        slug_to_uuid[s_str] = uuid.uuid5(uuid.NAMESPACE_OID, s_str)
            else:
                new_uid = uuid.uuid4()
                slug_to_uuid[str(new_uid)] = new_uid

        normalized = []
        for idx, s in enumerate(steps, start=1):
            raw_id = str(s.id).strip() if s.id else None
            step_uuid = slug_to_uuid.get(raw_id) if raw_id else uuid.uuid4()

            remapped_next = []
            for nid in (s.next_step_ids or []):
                nid_str = str(nid).strip()
                if nid_str in slug_to_uuid:
                    remapped_next.append(str(slug_to_uuid[nid_str]))
                else:
                    try:
                        remapped_next.append(str(UUID(nid_str)))
                    except ValueError:
                        remapped_next.append(str(uuid.uuid5(uuid.NAMESPACE_OID, nid_str)))

            step_order = s.step_order if s.step_order is not None else idx
            normalized.append({
                "id": step_uuid,
                "step_order": step_order,
                "type": s.type,
                "title": s.title,
                "description": s.description,
                "config": s.config,
                "next_step_ids": remapped_next,
            })
        return normalized

    async def _validate_step_configs_tenant(
        self,
        db: AsyncSession,
        organization_id: UUID,
        steps: Sequence[WorkflowStepCreate],
    ) -> None:
        """Enforces cross-tenant validation on referenced agents and knowledge sources."""
        for step in steps:
            cfg = step.config or {}
            # Validate agent reference if specified
            agent_id_raw = cfg.get("agent_id") or cfg.get("agentId")
            if agent_id_raw:
                try:
                    agent_uuid = UUID(str(agent_id_raw))
                    agent = await agent_repository.get_by_id(db, agent_uuid, load_relationships=False)
                    if not agent or agent.organization_id != organization_id:
                        raise NotFoundError(
                            f"Step '{step.title}' references Agent '{agent_id_raw}' which does not exist in this organization."
                        )
                except ValueError:
                    pass

            # Validate knowledge source reference if specified
            source_id_raw = (
                cfg.get("knowledge_source_id")
                or cfg.get("source_id")
                or cfg.get("sourceId")
            )
            if source_id_raw:
                try:
                    source_uuid = UUID(str(source_id_raw))
                    source = await knowledge_source_repository.get_by_id(db, source_uuid)
                    if not source or source.organization_id != organization_id:
                        raise NotFoundError(
                            f"Step '{step.title}' references Knowledge Source '{source_id_raw}' which does not exist in this organization."
                        )
                except ValueError:
                    pass

    async def _emit_audit_event(
        self,
        db: AsyncSession,
        organization_id: UUID,
        actor_id: Optional[UUID],
        action: str,
        workflow_id: UUID,
        details: Dict[str, Any],
        execution_id: Optional[UUID] = None,
    ) -> None:
        """Emits privacy-safe metadata audit record."""
        audit = AuditLog(
            id=uuid.uuid4(),
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
            resource_type="workflow_execution" if execution_id else "workflow",
            resource_id=execution_id or workflow_id,
            details={
                "workflow_id": str(workflow_id),
                **details,
            },
            created_at=datetime.now(timezone.utc),
        )
        db.add(audit)
        await db.flush()

    def _to_response(self, workflow: Workflow) -> WorkflowResponse:
        """Maps Workflow model to API response with calculated execution telemetry."""
        # Calculate executions telemetry
        total_execs = len(workflow.executions) if workflow.executions else 0
        completed_execs = sum(
            1 for e in (workflow.executions or []) if e.status == "completed"
        )
        success_rate = (
            f"{(completed_execs / total_execs) * 100:.1f}%" if total_execs > 0 else "100%"
        )

        last_run = "Never"
        if workflow.executions:
            sorted_execs = sorted(workflow.executions, key=lambda e: e.started_at, reverse=True)
            last_run = sorted_execs[0].started_at.strftime("%b %d, %Y")

        step_responses = [
            WorkflowStepResponse(
                id=s.id,
                workflow_id=s.workflow_id,
                step_order=s.step_order,
                type=s.type,
                title=s.title,
                description=s.description,
                config=s.config,
                next_step_ids=[UUID(str(nid)) for nid in (s.next_step_ids or [])],
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in (workflow.steps or [])
        ]

        return WorkflowResponse(
            id=workflow.id,
            organization_id=workflow.organization_id,
            created_by_user_id=workflow.created_by_user_id,
            name=workflow.name,
            description=workflow.description,
            status=workflow.status,
            trigger=workflow.trigger_type,
            trigger_type=workflow.trigger_type,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            steps=step_responses,
            executions=total_execs,
            success_rate=success_rate,
            last_run=last_run,
        )

    def _to_execution_response(self, execution: WorkflowExecution) -> WorkflowExecutionResponse:
        return WorkflowExecutionResponse(
            id=execution.id,
            workflow_id=execution.workflow_id,
            triggered_by_user_id=execution.triggered_by_user_id,
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            execution_log=execution.execution_log or [],
        )


workflow_service = WorkflowService()

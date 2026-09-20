from typing import List, Optional, Union
from uuid import UUID
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowStatusUpdate,
    WorkflowResponse,
    WorkflowStepCreate,
    WorkflowStepsSyncRequest,
    WorkflowExecutionResponse,
    WorkflowExecuteRequest,
    WorkflowApprovalRequest,
    WorkflowCancellationRequest,
)
from app.services.workflow_service import workflow_service

router = APIRouter()


# ==========================================
# Workflow Process Definition Endpoints
# ==========================================

@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Workflow",
    description="Creates a new automated workflow with an optional validated initial steps graph.",
)
async def create_workflow(
    payload: WorkflowCreate,
    db: AsyncSession = Depends(get_db_session),
) -> WorkflowResponse:
    return await workflow_service.create_workflow(db=db, schema=payload)


@router.get(
    "",
    response_model=List[WorkflowResponse],
    status_code=status.HTTP_200_OK,
    summary="List Workflows",
    description="Lists workflows belonging to a specific organization with pagination and computed metrics.",
)
async def list_workflows(
    organization_id: UUID = Query(..., description="Target organization ID"),
    status: Optional[str] = Query(None, description="Optional status filter ('Active', 'Draft', 'Paused')"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    db: AsyncSession = Depends(get_db_session),
) -> List[WorkflowResponse]:
    return await workflow_service.list_workflows(
        db=db,
        organization_id=organization_id,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Workflow Details",
    description="Retrieves a single workflow with full steps graph and execution telemetry.",
)
async def get_workflow(
    workflow_id: UUID,
    organization_id: Optional[UUID] = Query(None, description="Tenant organization isolation check"),
    db: AsyncSession = Depends(get_db_session),
) -> WorkflowResponse:
    return await workflow_service.get_workflow(
        db=db,
        workflow_id=workflow_id,
        organization_id=organization_id,
    )


@router.patch(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Workflow Metadata",
    description="Updates workflow name, description, status, or trigger category.",
)
async def update_workflow(
    workflow_id: UUID,
    payload: WorkflowUpdate,
    organization_id: Optional[UUID] = Query(None, description="Tenant organization isolation check"),
    db: AsyncSession = Depends(get_db_session),
) -> WorkflowResponse:
    return await workflow_service.update_workflow(
        db=db,
        workflow_id=workflow_id,
        schema=payload,
        organization_id=organization_id,
    )


@router.post(
    "/{workflow_id}/toggle-status",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle Workflow Status",
    description="Toggles workflow status between Active and Paused.",
)
async def toggle_workflow_status(
    workflow_id: UUID,
    organization_id: Optional[UUID] = Query(None, description="Tenant organization isolation check"),
    db: AsyncSession = Depends(get_db_session),
) -> WorkflowResponse:
    return await workflow_service.toggle_status(
        db=db,
        workflow_id=workflow_id,
        organization_id=organization_id,
    )


@router.patch(
    "/{workflow_id}/status",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Workflow Status",
    description="Directly sets workflow status to Active, Draft, or Paused.",
)
async def set_workflow_status(
    workflow_id: UUID,
    payload: WorkflowStatusUpdate,
    organization_id: Optional[UUID] = Query(None, description="Tenant organization isolation check"),
    db: AsyncSession = Depends(get_db_session),
) -> WorkflowResponse:
    return await workflow_service.update_workflow(
        db=db,
        workflow_id=workflow_id,
        schema=WorkflowUpdate(status=payload.status),
        organization_id=organization_id,
    )


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Workflow",
    description="Deletes a workflow and all associated steps and execution history.",
)
async def delete_workflow(
    workflow_id: UUID,
    organization_id: Optional[UUID] = Query(None, description="Tenant organization isolation check"),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    await workflow_service.delete_workflow(
        db=db,
        workflow_id=workflow_id,
        organization_id=organization_id,
    )


@router.put(
    "/{workflow_id}/steps",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Replace Workflow Steps Graph",
    description="Atomically replaces and validates the step graph for a workflow.",
)
async def replace_workflow_steps(
    workflow_id: UUID,
    payload: Union[List[WorkflowStepCreate], WorkflowStepsSyncRequest] = Body(...),
    organization_id: Optional[UUID] = Query(None, description="Tenant organization isolation check"),
    db: AsyncSession = Depends(get_db_session),
) -> WorkflowResponse:
    steps = payload.steps if isinstance(payload, WorkflowStepsSyncRequest) else payload
    return await workflow_service.replace_steps(
        db=db,
        workflow_id=workflow_id,
        steps=steps,
        organization_id=organization_id,
    )


# ==========================================
# Workflow Execution & Governance Endpoints
# ==========================================

@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Workflow",
    description="Triggers execution run for an Active workflow.",
)
async def execute_workflow(
    workflow_id: UUID,
    payload: Optional[WorkflowExecuteRequest] = None,
    organization_id: Optional[UUID] = Query(None, description="Tenant organization isolation check"),
    db: AsyncSession = Depends(get_db_session),
) -> WorkflowExecutionResponse:
    effective_org = organization_id or (payload.organization_id if payload else None)
    triggered_by = payload.triggered_by_user_id if payload else None
    return await workflow_service.execute_workflow(
        db=db,
        workflow_id=workflow_id,
        triggered_by_user_id=triggered_by,
        organization_id=effective_org,
    )


@router.get(
    "/{workflow_id}/executions",
    response_model=List[WorkflowExecutionResponse],
    status_code=status.HTTP_200_OK,
    summary="List Workflow Executions",
    description="Lists chronological execution runs for a specific workflow.",
)
async def list_workflow_executions(
    workflow_id: UUID,
    organization_id: Optional[UUID] = Query(None, description="Tenant organization isolation check"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    db: AsyncSession = Depends(get_db_session),
) -> List[WorkflowExecutionResponse]:
    return await workflow_service.list_executions(
        db=db,
        workflow_id=workflow_id,
        organization_id=organization_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Execution Details",
    description="Retrieves a single execution run with complete step logs.",
)
async def get_execution_detail(
    execution_id: UUID,
    organization_id: Optional[UUID] = Query(None, description="Tenant organization isolation check"),
    db: AsyncSession = Depends(get_db_session),
) -> WorkflowExecutionResponse:
    return await workflow_service.get_execution(
        db=db,
        execution_id=execution_id,
        organization_id=organization_id,
    )


@router.post(
    "/executions/{execution_id}/approve",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve Workflow Execution",
    description="Approves a workflow run paused in 'waiting_approval' and resumes traversal.",
)
async def approve_workflow_execution(
    execution_id: UUID,
    payload: WorkflowApprovalRequest,
    organization_id: Optional[UUID] = Query(None, description="Tenant organization isolation check"),
    db: AsyncSession = Depends(get_db_session),
) -> WorkflowExecutionResponse:
    return await workflow_service.approve_execution(
        db=db,
        execution_id=execution_id,
        payload=payload,
        organization_id=organization_id,
    )


@router.post(
    "/executions/{execution_id}/cancel",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel Workflow Execution",
    description="Cancels a running execution or rejects one waiting approval.",
)
async def cancel_workflow_execution(
    execution_id: UUID,
    payload: WorkflowCancellationRequest,
    organization_id: Optional[UUID] = Query(None, description="Tenant organization isolation check"),
    db: AsyncSession = Depends(get_db_session),
) -> WorkflowExecutionResponse:
    return await workflow_service.cancel_execution(
        db=db,
        execution_id=execution_id,
        payload=payload,
        organization_id=organization_id,
    )

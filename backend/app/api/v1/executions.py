from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.agent_execution import (
    AgentExecutionCreate,
    AgentExecutionResponse,
    ApprovalRequest,
    CancellationRequest,
)
from app.services.agent_execution_service import agent_execution_service

router = APIRouter()


# ==========================================
# Agent Execution Lifecycle Endpoints
# ==========================================

@router.post(
    "/agents/{agent_id}/executions",
    response_model=AgentExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger Agent Execution",
    description="Trigger an execution run for an active agent within an organization.",
)
async def create_agent_execution(
    agent_id: UUID,
    payload: AgentExecutionCreate,
    db: AsyncSession = Depends(get_db_session),
) -> AgentExecutionResponse:
    return await agent_execution_service.create_execution(
        db=db, agent_id=agent_id, schema=payload
    )


@router.get(
    "/agents/{agent_id}/executions",
    response_model=List[AgentExecutionResponse],
    status_code=status.HTTP_200_OK,
    summary="List Agent Executions",
    description="List execution runs for a specific agent, optionally filtered by status.",
)
async def list_agent_executions(
    agent_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    status: str | None = Query(None, description="Filter executions by status"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    db: AsyncSession = Depends(get_db_session),
) -> List[AgentExecutionResponse]:
    return await agent_execution_service.list_executions_by_agent(
        db=db,
        agent_id=agent_id,
        organization_id=organization_id,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/executions/{execution_id}",
    response_model=AgentExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Execution Status",
    description="Retrieve execution state, output, and metrics by execution UUID.",
)
async def get_execution(
    execution_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> AgentExecutionResponse:
    return await agent_execution_service.get_execution(
        db=db, execution_id=execution_id, organization_id=organization_id
    )


@router.post(
    "/executions/{execution_id}/approve",
    response_model=AgentExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve Execution",
    description="Grant human approval to an execution waiting in 'waiting_for_approval' state.",
)
async def approve_execution(
    execution_id: UUID,
    payload: ApprovalRequest,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> AgentExecutionResponse:
    return await agent_execution_service.approve_execution(
        db=db,
        execution_id=execution_id,
        payload=payload,
        organization_id=organization_id,
    )


@router.post(
    "/executions/{execution_id}/cancel",
    response_model=AgentExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel Execution",
    description="Cancel a running or pending execution, or reject one waiting for approval.",
)
async def cancel_execution(
    execution_id: UUID,
    payload: CancellationRequest,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> AgentExecutionResponse:
    return await agent_execution_service.cancel_execution(
        db=db,
        execution_id=execution_id,
        payload=payload,
        organization_id=organization_id,
    )

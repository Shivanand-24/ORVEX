from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.agent import (
    AgentCreate,
    AgentKnowledgeSourceAttach,
    AgentResponse,
    AgentToolAttach,
    AgentUpdate,
)
from app.schemas.knowledge import KnowledgeSourceResponse
from app.services.agent_service import agent_service

router = APIRouter()


# ==========================================
# Agent CRUD Endpoints
# ==========================================

@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Agent",
    description="Register and configure a new AI Agent for an organization.",
)
async def create_agent(
    payload: AgentCreate,
    db: AsyncSession = Depends(get_db_session),
) -> AgentResponse:
    return await agent_service.create_agent(db, payload)


@router.get(
    "",
    response_model=List[AgentResponse],
    status_code=status.HTTP_200_OK,
    summary="List Agents",
    description="List AI agents, optionally filtered by organization ID, domain, and status.",
)
async def list_agents(
    organization_id: UUID | None = Query(None, description="Filter agents by organization ID"),
    domain: str | None = Query(None, description="Filter agents by operational domain"),
    status_filter: str | None = Query(None, alias="status", description="Filter agents by status ('Active', 'Paused')"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    db: AsyncSession = Depends(get_db_session),
) -> List[AgentResponse]:
    return await agent_service.list_agents(
        db,
        organization_id=organization_id,
        domain=domain,
        status=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Agent",
    description="Retrieve an agent by UUID.",
)
async def get_agent(
    agent_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> AgentResponse:
    return await agent_service.get_agent(
        db, agent_id, organization_id=organization_id
    )


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Agent",
    description="Update agent configuration fields (name, description, domain, status, instructions, require_approval).",
)
async def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> AgentResponse:
    return await agent_service.update_agent(
        db, agent_id, payload, organization_id=organization_id
    )


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Agent",
    description="Delete an agent entity and cascade delete all associated tool and knowledge source attachments.",
)
async def delete_agent(
    agent_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    await agent_service.delete_agent(
        db, agent_id, organization_id=organization_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==========================================
# Knowledge Source Relationship Endpoints
# ==========================================

@router.get(
    "/{agent_id}/knowledge-sources",
    response_model=List[KnowledgeSourceResponse],
    status_code=status.HTTP_200_OK,
    summary="List Agent Knowledge Sources",
    description="List all knowledge sources currently attached to this agent.",
)
async def list_agent_knowledge_sources(
    agent_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> List[KnowledgeSourceResponse]:
    return await agent_service.list_agent_knowledge_sources(
        db, agent_id, organization_id=organization_id
    )


@router.post(
    "/{agent_id}/knowledge-sources",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Attach Knowledge Source to Agent",
    description="Associate a knowledge source with an agent within the same organization.",
)
async def attach_knowledge_source(
    agent_id: UUID,
    payload: AgentKnowledgeSourceAttach,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> KnowledgeSourceResponse:
    return await agent_service.attach_knowledge_source(
        db, agent_id, payload.source_id, organization_id=organization_id
    )


@router.delete(
    "/{agent_id}/knowledge-sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Detach Knowledge Source from Agent",
    description="Remove the association between an agent and a knowledge source.",
)
async def detach_knowledge_source(
    agent_id: UUID,
    source_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    await agent_service.detach_knowledge_source(
        db, agent_id, source_id, organization_id=organization_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==========================================
# Tool Relationship Endpoints
# ==========================================

@router.get(
    "/{agent_id}/tools",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="List Agent Tools",
    description="List all registered tool identifiers associated with an agent.",
)
async def list_agent_tools(
    agent_id: UUID,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> List[str]:
    return await agent_service.list_agent_tools(
        db, agent_id, organization_id=organization_id
    )


@router.post(
    "/{agent_id}/tools",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Attach Tool to Agent",
    description="Associate an application tool identifier with an agent.",
)
async def attach_tool(
    agent_id: UUID,
    payload: AgentToolAttach,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    tool_name = await agent_service.attach_tool(
        db, agent_id, payload.tool_name, organization_id=organization_id
    )
    return {"agent_id": str(agent_id), "tool_name": tool_name}


@router.delete(
    "/{agent_id}/tools/{tool_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Detach Tool from Agent",
    description="Remove a tool association from an agent.",
)
async def detach_tool(
    agent_id: UUID,
    tool_name: str,
    organization_id: UUID | None = Query(None, description="Enforce tenant organization isolation"),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    await agent_service.detach_tool(
        db, agent_id, tool_name, organization_id=organization_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

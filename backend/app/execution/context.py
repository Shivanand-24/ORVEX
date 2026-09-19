import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from app.execution.lifecycle import ExecutionStatus


@dataclass
class ExecutionContext:
    """Ephemeral runtime-only execution state.

    NOTE: This is NOT the database source of truth. The persistent database record
    is represented by the AgentExecution model. ExecutionContext carries runtime
    parameters, trace correlation tokens, and in-memory caches across execution pipeline steps.
    """

    execution_id: UUID
    organization_id: UUID
    agent_id: UUID
    input_prompt: str
    status: ExecutionStatus
    triggered_by_user_id: UUID | None = None
    source: str = "direct_api"
    source_reference_id: UUID | None = None
    require_approval: bool = False
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    assembled_system_prompt: str = ""
    authorized_tools: list[str] = field(default_factory=list)
    authorized_knowledge_sources: list[UUID] = field(default_factory=list)
    retrieved_knowledge_context: str = ""
    intermediate_tool_results: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_tool_result(self, result: dict) -> None:
        self.intermediate_tool_results.append(result)


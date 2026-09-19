from abc import ABC, abstractmethod
from typing import Any, Sequence
from uuid import UUID

from app.execution.context import ExecutionContext


class KnowledgeProvider(ABC):
    """Abstract interface for querying tenant-authorized knowledge collections."""

    @abstractmethod
    async def retrieve_context(
        self,
        organization_id: UUID,
        source_ids: Sequence[UUID],
        query: str,
        limit: int = 5,
    ) -> str:
        """Retrieve relevant context chunks from authorized knowledge sources."""
        pass


class ToolRegistry(ABC):
    """Abstract interface for resolving and dispatching application tools."""

    @abstractmethod
    def is_tool_authorized(self, authorized_tools: Sequence[str], tool_name: str) -> bool:
        """Verify that the requested tool is in the agent's authorized tools list."""
        pass

    @abstractmethod
    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """Execute a registered tool in a sandboxed runtime and return structured output."""
        pass


class LLMProvider(ABC):
    """Abstract interface for provider-agnostic model reasoning and text generation."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: ExecutionContext,
    ) -> str:
        """Generate response text for the given prompt and execution context."""
        pass

import asyncio
import time
from typing import Optional

from app.llm.interfaces import BaseLLMProvider
from app.llm.schemas import LLMRequest, LLMResponse, LLMUsage, ProviderMetadata


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for offline development and test suites."""

    def __init__(
        self,
        default_response: Optional[str] = None,
        default_model: str = "mock-model",
        simulated_latency_ms: int = 10,
    ) -> None:
        self.default_response = default_response
        self.default_model = default_model
        self.simulated_latency_ms = max(0, simulated_latency_ms)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        start_time = time.perf_counter()

        if self.simulated_latency_ms > 0:
            await asyncio.sleep(self.simulated_latency_ms / 1000.0)

        # Extract last user message
        last_user_message = ""
        total_prompt_chars = 0
        if request.system_instruction:
            total_prompt_chars += len(request.system_instruction)

        for m in request.messages:
            total_prompt_chars += len(m.content)
            if m.role == "user":
                last_user_message = m.content

        # Determine response text
        if self.default_response:
            content = self.default_response
        else:
            if not last_user_message:
                content = "Hello! I am ORVEX AI Assistant. How can I help you today?"
            else:
                content = f"ORVEX Assistant response to: '{last_user_message}'"

        # Calculate deterministic token usage (~4 chars/token)
        input_tokens = max(1, total_prompt_chars // 4)
        output_tokens = max(1, len(content) // 4)
        total_tokens = input_tokens + output_tokens

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        target_model = request.model or self.default_model

        return LLMResponse(
            content=content,
            model=target_model,
            provider="mock",
            usage=LLMUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            ),
            finish_reason="stop",
            latency_ms=elapsed_ms,
        )

    def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name="mock",
            default_model=self.default_model,
            supported_models=["mock-model", "mock-fast", "mock-advanced"],
        )

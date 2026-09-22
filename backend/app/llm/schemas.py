from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class LLMMessage(BaseModel):
    """Normalized chat message structure for LLM generation."""

    role: str = Field(..., description="Message role: 'system', 'user', or 'assistant'")
    content: str = Field(..., min_length=1, description="Message text content")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized not in ("system", "user", "assistant"):
            raise ValueError(f"Invalid message role '{v}'. Must be 'system', 'user', or 'assistant'.")
        return normalized

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Message content cannot be empty or whitespace.")
        return trimmed


class LLMRequest(BaseModel):
    """Normalized request payload passed to LLM providers."""

    messages: List[LLMMessage] = Field(..., min_length=1, description="Chronological chat message history")
    system_instruction: Optional[str] = Field(None, description="Optional system instruction / persona prompt")
    model: Optional[str] = Field(None, description="Target model identifier (overrides default)")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=128000, description="Maximum tokens to generate")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic and correlation metadata")

    model_config = ConfigDict(extra="ignore")


class LLMUsage(BaseModel):
    """Normalized token telemetry from provider generation."""

    input_tokens: int = Field(0, ge=0, description="Prompt tokens consumed")
    output_tokens: int = Field(0, ge=0, description="Completion tokens generated")
    total_tokens: int = Field(0, ge=0, description="Total tokens consumed")

    @field_validator("total_tokens", mode="before")
    @classmethod
    def compute_total_if_missing(cls, v: Any, info: Any) -> int:
        if v is not None and int(v) > 0:
            return int(v)
        # Fallback to sum of input and output tokens
        return 0


class LLMResponse(BaseModel):
    """Normalized response payload returned by LLM providers."""

    content: str = Field(..., description="Model response text")
    model: str = Field(..., description="Actual model that generated the response")
    provider: str = Field(..., description="Provider identifier (e.g., 'openai', 'mock')")
    usage: LLMUsage = Field(default_factory=LLMUsage, description="Token consumption metrics")
    finish_reason: Optional[str] = Field(None, description="Reason for stopping generation")
    latency_ms: int = Field(0, ge=0, description="Total generation duration in milliseconds")

    model_config = ConfigDict(extra="ignore")


class ProviderMetadata(BaseModel):
    """Metadata describing provider capabilities and defaults."""

    name: str
    default_model: str
    supported_models: List[str] = Field(default_factory=list)

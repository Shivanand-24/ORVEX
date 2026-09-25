import logging
import time
from typing import Optional
import httpx

from app.llm.errors import (
    ConfigurationError,
    ProviderRequestError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)
from app.llm.interfaces import BaseLLMProvider
from app.llm.schemas import LLMRequest, LLMResponse, LLMUsage, ProviderMetadata

logger = logging.getLogger(__name__)

DEFAULT_ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
DEFAULT_ANTHROPIC_VERSION = "2023-06-01"


class ClaudeProvider(BaseLLMProvider):
    """Native Anthropic Claude API provider using /messages."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: float = 30.0,
        client: Optional[httpx.AsyncClient] = None,
        anthropic_version: str = DEFAULT_ANTHROPIC_VERSION,
    ) -> None:
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_ANTHROPIC_BASE_URL).rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self._client = client
        self.anthropic_version = anthropic_version

    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Validate API Key
        effective_key = self.api_key
        if not effective_key:
            raise ConfigurationError(
                detail="AI service configuration is invalid or missing credentials.",
                internal_error="ANTHROPIC_API_KEY is not configured for Claude provider.",
            )

        # Validate Model Configuration (no obsolete hardcoded model fallback)
        target_model = request.model or self.default_model
        if not target_model:
            raise ConfigurationError(
                detail="AI service configuration is invalid or missing model.",
                internal_error="LLM_MODEL is not configured for Claude provider.",
            )

        headers = {
            "x-api-key": effective_key,
            "anthropic-version": self.anthropic_version,
            "Content-Type": "application/json",
        }

        # Map system instructions and conversational messages
        # Anthropic Messages API takes top-level "system", while "messages" only accepts user and assistant roles
        system_parts = []
        if request.system_instruction:
            system_parts.append(request.system_instruction)

        claude_messages = []
        for m in request.messages:
            if m.role == "system":
                system_parts.append(m.content)
            else:
                claude_messages.append({"role": m.role, "content": m.content})

        max_tokens = request.max_tokens or 2048
        payload: dict = {
            "model": target_model,
            "messages": claude_messages,
            "max_tokens": max_tokens,
        }

        if system_parts:
            payload["system"] = "\n\n".join(system_parts)

        if request.temperature is not None:
            payload["temperature"] = request.temperature

        url = f"{self.base_url}/messages" if self.base_url.endswith("/v1") else f"{self.base_url}/v1/messages"
        start_time = time.perf_counter()

        try:
            if self._client is not None:
                response = await self._client.post(url, json=payload, headers=headers, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)

            response.raise_for_status()

        except httpx.TimeoutException as exc:
            logger.warning("Claude request timed out for model %s: %s", target_model, exc)
            raise ProviderTimeoutError(
                detail="AI service request timed out. Please try again.",
                internal_error=f"Timeout contacting {url}",
            ) from exc

        except httpx.ConnectError as exc:
            logger.warning("Failed to connect to Claude provider at %s: %s", url, exc)
            raise ProviderUnavailableError(
                detail="AI service is temporarily unavailable. Please try again later.",
                internal_error=f"ConnectError contacting {url}",
            ) from exc

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("Claude provider returned HTTP status %d for model %s", status, target_model)

            if status in (401, 403):
                raise ConfigurationError(
                    detail="AI service authentication failed.",
                    internal_error=f"Claude provider rejected API key with HTTP {status}.",
                ) from exc

            if status == 429:
                raise RateLimitError(
                    detail="AI service rate limit exceeded. Please retry shortly.",
                    internal_error=f"Rate limited by Claude provider with HTTP {status}.",
                ) from exc

            if status in (400, 422):
                raise ProviderRequestError(
                    detail="AI request could not be processed by the provider.",
                    internal_error=f"Invalid request rejected with HTTP {status}.",
                ) from exc

            if status >= 500:
                raise ProviderUnavailableError(
                    detail="AI service is temporarily unavailable. Please try again later.",
                    internal_error=f"Claude provider server error with HTTP {status}.",
                ) from exc

            raise ProviderRequestError(
                detail="AI request could not be processed by the provider.",
                internal_error=f"HTTP status {status}",
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected error communicating with Claude provider at %s", url)
            raise ProviderUnavailableError(
                detail="AI service is temporarily unavailable. Please try again later.",
                internal_error=str(exc),
            ) from exc

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        try:
            data = response.json()
            content_blocks = data.get("content", [])
            if not isinstance(content_blocks, list) or not content_blocks:
                raise ProviderRequestError(
                    detail="AI provider returned an empty completion response.",
                    internal_error="No content blocks in response payload.",
                )

            text_parts = [
                block.get("text", "")
                for block in content_blocks
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            content = "".join(text_parts)

            if not content:
                raise ProviderRequestError(
                    detail="AI provider returned an empty completion response.",
                    internal_error="Empty text content in response blocks.",
                )

            finish_reason = data.get("stop_reason")

            raw_usage = data.get("usage", {})
            input_tokens = raw_usage.get("input_tokens", 0)
            output_tokens = raw_usage.get("output_tokens", 0)
            total_tokens = raw_usage.get("total_tokens", input_tokens + output_tokens)

            return LLMResponse(
                content=content,
                model=data.get("model", target_model),
                provider="claude",
                usage=LLMUsage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                ),
                finish_reason=finish_reason,
                latency_ms=elapsed_ms,
            )

        except (KeyError, ValueError) as exc:
            logger.exception("Failed to parse Claude provider response from %s", url)
            raise ProviderRequestError(
                detail="AI service returned an unreadable response format.",
                internal_error=str(exc),
            ) from exc

    def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name="claude",
            default_model=self.default_model or "",
            supported_models=[self.default_model] if self.default_model else [],
        )

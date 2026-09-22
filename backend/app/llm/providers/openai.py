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

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI and OpenAI-compatible API provider using /chat/completions."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = DEFAULT_OPENAI_MODEL,
        timeout: float = 30.0,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_OPENAI_BASE_URL).rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self._client = client

    def _is_local_endpoint(self) -> bool:
        url = self.base_url.lower()
        return "localhost" in url or "127.0.0.1" in url or "0.0.0.0" in url or "ollama" in url

    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Validate API Key
        effective_key = self.api_key
        if not effective_key:
            if self._is_local_endpoint():
                effective_key = "local-no-key"
            else:
                raise ConfigurationError(
                    detail="AI service configuration is invalid or missing credentials.",
                    internal_error="LLM_API_KEY is not configured for remote OpenAI provider.",
                )

        headers = {
            "Authorization": f"Bearer {effective_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if request.system_instruction:
            messages.append({"role": "system", "content": request.system_instruction})
        for m in request.messages:
            messages.append({"role": m.role, "content": m.content})

        target_model = request.model or self.default_model
        payload = {
            "model": target_model,
            "messages": messages,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        url = f"{self.base_url}/chat/completions"
        start_time = time.perf_counter()

        try:
            if self._client is not None:
                response = await self._client.post(url, json=payload, headers=headers, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)

            response.raise_for_status()

        except httpx.TimeoutException as exc:
            logger.warning("LLM request timed out for model %s: %s", target_model, exc)
            raise ProviderTimeoutError(
                detail="AI service request timed out. Please try again.",
                internal_error=f"Timeout contacting {url}",
            ) from exc

        except httpx.ConnectError as exc:
            logger.warning("Failed to connect to LLM provider at %s: %s", url, exc)
            raise ProviderUnavailableError(
                detail="AI service is temporarily unavailable. Please try again later.",
                internal_error=f"ConnectError contacting {url}",
            ) from exc

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("LLM provider returned HTTP status %d for model %s", status, target_model)

            if status in (401, 403):
                raise ConfigurationError(
                    detail="AI service authentication failed.",
                    internal_error=f"Provider rejected API key with HTTP {status}.",
                ) from exc

            if status == 429:
                raise RateLimitError(
                    detail="AI service rate limit exceeded. Please retry shortly.",
                    internal_error=f"Rate limited by provider with HTTP {status}.",
                ) from exc

            if status in (400, 422):
                raise ProviderRequestError(
                    detail="AI request could not be processed by the provider.",
                    internal_error=f"Invalid request rejected with HTTP {status}.",
                ) from exc

            if status >= 500:
                raise ProviderUnavailableError(
                    detail="AI service is temporarily unavailable. Please try again later.",
                    internal_error=f"Provider server error with HTTP {status}.",
                ) from exc

            raise ProviderRequestError(
                detail="AI request could not be processed by the provider.",
                internal_error=f"HTTP status {status}",
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected error communicating with LLM provider at %s", url)
            raise ProviderUnavailableError(
                detail="AI service is temporarily unavailable. Please try again later.",
                internal_error=str(exc),
            ) from exc

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        try:
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise ProviderRequestError(
                    detail="AI provider returned an empty completion response.",
                    internal_error="No choices in response payload.",
                )

            choice = choices[0]
            content = choice.get("message", {}).get("content", "")
            finish_reason = choice.get("finish_reason")

            raw_usage = data.get("usage", {})
            prompt_tokens = raw_usage.get("prompt_tokens", 0)
            completion_tokens = raw_usage.get("completion_tokens", 0)
            total_tokens = raw_usage.get("total_tokens", prompt_tokens + completion_tokens)

            return LLMResponse(
                content=content,
                model=data.get("model", target_model),
                provider="openai",
                usage=LLMUsage(
                    input_tokens=prompt_tokens,
                    output_tokens=completion_tokens,
                    total_tokens=total_tokens,
                ),
                finish_reason=finish_reason,
                latency_ms=elapsed_ms,
            )

        except (KeyError, ValueError) as exc:
            logger.exception("Failed to parse provider response from %s", url)
            raise ProviderRequestError(
                detail="AI service returned an unreadable response format.",
                internal_error=str(exc),
            ) from exc

    def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name="openai",
            default_model=self.default_model,
            supported_models=[
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
            ],
        )

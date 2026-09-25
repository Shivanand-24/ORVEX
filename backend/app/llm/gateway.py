import logging
from typing import Optional

from app.core.config import Settings, settings as default_settings
from app.llm.errors import ConfigurationError
from app.llm.interfaces import BaseLLMProvider
from app.llm.providers.claude import ClaudeProvider
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.openai import OpenAIProvider
from app.llm.schemas import LLMRequest, LLMResponse, ProviderMetadata

logger = logging.getLogger(__name__)


class LLMGateway:
    """Stateless LLM Gateway for provider dispatch, request normalization, and error translation."""

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self._settings = settings or default_settings
        self._provider = provider or self._resolve_provider(self._settings)

    @classmethod
    def _resolve_provider(cls, settings: Settings) -> BaseLLMProvider:
        provider_name = (settings.LLM_PROVIDER or "mock").strip().lower()

        if provider_name == "mock":
            return MockLLMProvider(
                default_model=settings.LLM_MODEL or "mock-model",
            )

        if provider_name in ("openai", "openai-compatible"):
            api_key = settings.OPENAI_API_KEY or settings.LLM_API_KEY
            return OpenAIProvider(
                api_key=api_key,
                base_url=settings.LLM_API_BASE_URL,
                default_model=settings.LLM_MODEL or "gpt-4o-mini",
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )

        if provider_name in ("claude", "anthropic"):
            api_key = settings.ANTHROPIC_API_KEY or settings.LLM_API_KEY
            return ClaudeProvider(
                api_key=api_key,
                base_url=settings.LLM_API_BASE_URL,
                default_model=settings.LLM_MODEL,
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )

        raise ConfigurationError(
            detail=f"Unsupported LLM provider '{settings.LLM_PROVIDER}'.",
            internal_error=f"Provider '{settings.LLM_PROVIDER}' is not recognized.",
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Executes a generation request through the configured provider with defaults."""
        effective_model = request.model or self._settings.LLM_MODEL
        effective_temp = request.temperature if request.temperature is not None else self._settings.LLM_TEMPERATURE
        effective_max_tokens = request.max_tokens if request.max_tokens is not None else self._settings.LLM_MAX_TOKENS

        normalized_request = LLMRequest(
            messages=request.messages,
            system_instruction=request.system_instruction,
            model=effective_model,
            temperature=effective_temp,
            max_tokens=effective_max_tokens,
            metadata=request.metadata,
        )

        logger.info(
            "Dispatching LLM generation request (provider=%s, model=%s, messages=%d)",
            self._provider.get_metadata().name,
            effective_model,
            len(normalized_request.messages),
        )

        response = await self._provider.generate(normalized_request)

        logger.info(
            "LLM generation completed (provider=%s, model=%s, tokens=%d, latency=%dms)",
            response.provider,
            response.model,
            response.usage.total_tokens,
            response.latency_ms,
        )

        return response

    def get_metadata(self) -> ProviderMetadata:
        """Returns the active provider's metadata."""
        return self._provider.get_metadata()


def get_llm_gateway() -> LLMGateway:
    """Dependency provider factory returning a stateless LLMGateway instance."""
    return LLMGateway()

from abc import ABC, abstractmethod
from app.llm.schemas import LLMRequest, LLMResponse, ProviderMetadata


class BaseLLMProvider(ABC):
    """Abstract interface defining the contract for all ORVEX LLM providers."""

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a model completion for the normalized LLM request."""
        pass

    @abstractmethod
    def get_metadata(self) -> ProviderMetadata:
        """Return provider identification, default model, and supported features."""
        pass

from abc import ABC, abstractmethod
from app.embeddings.schemas import (
    EmbeddingBatchRequest,
    EmbeddingBatchResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)


class BaseEmbeddingProvider(ABC):
    """Abstract interface defining the contract for all ORVEX embedding providers.

    Decouples embedding generation from specific upstream services (e.g. Mock, Gemini,
    OpenAI, or local embedding models).
    """

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate a dense float vector embedding for the input text."""
        pass

    async def embed_batch(self, request: EmbeddingBatchRequest) -> EmbeddingBatchResponse:
        """Generate dense float vector embeddings for a batch of input texts."""
        embeddings = []
        for text in request.inputs:
            single_req = EmbeddingRequest(
                input=text,
                model=request.model,
                dimensions=request.dimensions,
            )
            resp = await self.embed(single_req)
            embeddings.append(resp.embedding)

        dimensions = len(embeddings[0]) if embeddings else (request.dimensions or 0)
        model = request.model or getattr(self, "default_model", "unknown")
        provider = getattr(self, "provider_name", "unknown")

        return EmbeddingBatchResponse(
            embeddings=embeddings,
            dimensions=dimensions,
            model=model,
            provider=provider,
            count=len(embeddings),
        )

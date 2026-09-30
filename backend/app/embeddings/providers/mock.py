import hashlib
from typing import List, Optional

from app.embeddings.interfaces import BaseEmbeddingProvider
from app.embeddings.schemas import EmbeddingRequest, EmbeddingResponse


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic mock embedding provider for testing and offline development.

    Uses SHA-256 pseudo-random expansion to deterministically synthesize float vectors
    bounded within [-1.0, 1.0]. Avoids external network calls, tokenizers, or random state.
    """

    def __init__(
        self,
        default_model: str = "mock-embedding",
        default_dimensions: int = 384,
    ) -> None:
        self.default_model = default_model
        self.default_dimensions = max(1, default_dimensions)
        self.provider_name = "mock"

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generates a deterministic float vector embedding for the input text."""
        model = request.model or self.default_model
        dimensions = request.dimensions or self.default_dimensions

        embedding = self._generate_vector(
            text=request.input,
            model=model,
            dimensions=dimensions,
        )

        return EmbeddingResponse(
            embedding=embedding,
            dimensions=dimensions,
            model=model,
            provider=self.provider_name,
        )

    def _generate_vector(self, text: str, model: str, dimensions: int) -> List[float]:
        """Generates a deterministic float vector using SHA-256 hash blocks."""
        vector: List[float] = []
        counter = 0

        while len(vector) < dimensions:
            seed = f"{model}:{counter}:{text}".encode("utf-8")
            digest = hashlib.sha256(seed).digest()

            # 32 bytes yields 8 4-byte signed integers
            for offset in range(0, 32, 4):
                if len(vector) >= dimensions:
                    break
                int_val = int.from_bytes(digest[offset : offset + 4], byteorder="big", signed=True)
                float_val = round(int_val / 2147483647.0, 6)
                vector.append(float_val)

            counter += 1

        return vector

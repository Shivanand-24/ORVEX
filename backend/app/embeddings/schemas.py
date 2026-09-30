from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EmbeddingRequest(BaseModel):
    """Normalized single-text request payload passed to embedding providers."""

    input: str = Field(..., description="Text content to embed")
    model: Optional[str] = Field(None, description="Target embedding model (overrides default)")
    dimensions: Optional[int] = Field(None, ge=1, description="Target vector dimension count")

    model_config = ConfigDict(extra="ignore")

    @field_validator("input")
    @classmethod
    def validate_input_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Input text cannot be empty or whitespace-only.")
        return trimmed

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Dimensions must be greater than 0.")
        return v


class EmbeddingResponse(BaseModel):
    """Normalized response payload returned by embedding providers."""

    embedding: List[float] = Field(..., description="Dense float vector representation")
    dimensions: int = Field(..., ge=1, description="Declared dimensionality of the embedding vector")
    model: str = Field(..., description="Actual model that generated the embedding")
    provider: str = Field(..., description="Provider identifier (e.g., 'mock')")

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_embedding_dimensions(self) -> "EmbeddingResponse":
        if len(self.embedding) != self.dimensions:
            raise ValueError(
                f"Embedding vector length ({len(self.embedding)}) does not match declared dimensions ({self.dimensions})."
            )
        return self


class EmbeddingBatchRequest(BaseModel):
    """Normalized batch request payload passed to embedding providers."""

    inputs: List[str] = Field(..., min_length=1, description="List of texts to embed")
    model: Optional[str] = Field(None, description="Target embedding model (overrides default)")
    dimensions: Optional[int] = Field(None, ge=1, description="Target vector dimension count")

    model_config = ConfigDict(extra="ignore")

    @field_validator("inputs")
    @classmethod
    def validate_inputs_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Inputs list cannot be empty.")
        cleaned = []
        for i, text in enumerate(v):
            trimmed = text.strip()
            if not trimmed:
                raise ValueError(f"Input at index {i} cannot be empty or whitespace-only.")
            cleaned.append(trimmed)
        return cleaned

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Dimensions must be greater than 0.")
        return v


class EmbeddingBatchResponse(BaseModel):
    """Normalized batch response payload returned by embedding providers."""

    embeddings: List[List[float]] = Field(..., description="Dense float vectors corresponding to inputs")
    dimensions: int = Field(..., ge=1, description="Declared dimensionality of the embedding vectors")
    model: str = Field(..., description="Actual model that generated the embeddings")
    provider: str = Field(..., description="Provider identifier (e.g., 'mock')")
    count: int = Field(..., ge=1, description="Total number of embeddings in batch")

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_batch_dimensions(self) -> "EmbeddingBatchResponse":
        if len(self.embeddings) != self.count:
            raise ValueError(
                f"Number of embeddings ({len(self.embeddings)}) does not match declared count ({self.count})."
            )
        for i, vec in enumerate(self.embeddings):
            if len(vec) != self.dimensions:
                raise ValueError(
                    f"Embedding at index {i} length ({len(vec)}) does not match declared dimensions ({self.dimensions})."
                )
        return self

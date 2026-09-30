from abc import ABC, abstractmethod
from app.rag.schemas import RetrievalRequest, RetrievalResult


class BaseRetriever(ABC):
    """Abstract provider-neutral interface defining the contract for all ORVEX retrievers.

    Decouples retrieval consumption from specific indexing and search backends
    (e.g., in-memory mock, lexical search, pgvector, or external vector stores).
    """

    @abstractmethod
    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Retrieve relevant chunks matching the request criteria."""
        pass

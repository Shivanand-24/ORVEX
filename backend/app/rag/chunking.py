import uuid
from typing import List
from app.rag.schemas import Chunk

DEFAULT_CHUNK_SIZE: int = 500
DEFAULT_CHUNK_OVERLAP: int = 50


class TextChunker:
    """Deterministic text chunking utility for RAG indexing.

    Partitions raw document text into overlapping character-level chunks with
    explicit character boundary offsets. Preserves original text content without
    external tokenizer or AI dependencies.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be greater than 0, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be non-negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[Chunk]:
        """Splits document text into deterministic chunks.

        Handles empty/whitespace input safely by returning an empty list.
        Preserves original text content within exact character offsets.
        """
        if not text or not text.strip():
            return []

        text_length = len(text)
        step = self.chunk_size - self.chunk_overlap
        chunks: List[Chunk] = []
        chunk_index = 0
        start = 0

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            content = text[start:end]

            # Generate deterministic UUID5 based on text slice and offsets
            deterministic_id = uuid.uuid5(
                uuid.NAMESPACE_OID,
                f"orvex:rag:chunk:{chunk_index}:{start}:{end}:{content}",
            )

            chunks.append(
                Chunk(
                    chunk_id=deterministic_id,
                    content=content,
                    character_start=start,
                    character_end=end,
                    chunk_index=chunk_index,
                )
            )

            chunk_index += 1
            if end >= text_length:
                break

            start += step

        return chunks


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Chunk]:
    """Convenience functional wrapper around TextChunker."""
    return TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap).chunk_text(text)

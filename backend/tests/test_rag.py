import uuid
import pytest

from app.rag import (
    Chunk,
    ContextBuilder,
    MockRetriever,
    RetrievalChunk,
    RetrievalRequest,
    RetrievalResult,
    RetrievedContext,
    TextChunker,
    build_retrieved_context,
    chunk_text,
)


# ==============================================================================
# 1. Chunking Tests
# ==============================================================================

def test_chunking_empty_text():
    assert chunk_text("") == []


def test_chunking_whitespace_text():
    assert chunk_text("   \n\t  \r\n   ") == []


def test_chunking_short_text():
    text = "ORVEX Enterprise Copilot."
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.content == text
    assert chunk.character_start == 0
    assert chunk.character_end == len(text)
    assert chunk.chunk_index == 0
    assert isinstance(chunk.chunk_id, uuid.UUID)


def test_chunking_exact_chunk_boundary():
    chunk_size = 50
    text = "A" * chunk_size
    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=10)

    assert len(chunks) == 1
    assert chunks[0].content == text
    assert chunks[0].character_start == 0
    assert chunks[0].character_end == chunk_size
    assert chunks[0].chunk_index == 0


def test_chunking_long_text():
    sentence = "Security guidelines and access control policies for enterprise users. "
    text = sentence * 20  # ~1400 characters
    chunk_size = 200
    chunk_overlap = 40

    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    assert len(chunks) > 1

    # Verify monotonic index sequence
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert len(chunk.content) <= chunk_size
        assert chunk.character_start < chunk.character_end

    # Last chunk reaches end of text
    assert chunks[-1].character_end == len(text)


def test_chunking_overlap_behavior():
    text = "0123456789abcdefghij"  # 20 chars
    chunk_size = 10
    chunk_overlap = 4  # step = 6

    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    # Expected:
    # Chunk 0: [0:10]  -> "0123456789"
    # Chunk 1: [6:16]  -> "6789abcdef" (overlap "6789")
    # Chunk 2: [12:20] -> "cdefghij"   (overlap "cdef")
    assert len(chunks) == 3

    assert chunks[0].content == "0123456789"
    assert chunks[0].character_start == 0
    assert chunks[0].character_end == 10

    assert chunks[1].content == "6789abcdef"
    assert chunks[1].character_start == 6
    assert chunks[1].character_end == 16
    # Verify overlap characters between 0 and 1
    assert chunks[0].content[-4:] == chunks[1].content[:4]

    assert chunks[2].content == "cdefghij"
    assert chunks[2].character_start == 12
    assert chunks[2].character_end == 20
    # Verify overlap characters between 1 and 2
    assert chunks[1].content[-4:] == chunks[2].content[:4]


def test_chunking_deterministic_output():
    text = "Enterprise architecture specification for distributed intelligence systems."
    chunks_1 = chunk_text(text, chunk_size=30, chunk_overlap=10)
    chunks_2 = chunk_text(text, chunk_size=30, chunk_overlap=10)

    assert len(chunks_1) == len(chunks_2)
    for c1, c2 in zip(chunks_1, chunks_2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.content == c2.content
        assert c1.character_start == c2.character_start
        assert c1.character_end == c2.character_end
        assert c1.chunk_index == c2.chunk_index


def test_chunking_character_offsets():
    text = "The quick brown fox jumps over the lazy dog repeatedly until sunset."
    chunks = chunk_text(text, chunk_size=25, chunk_overlap=8)

    for chunk in chunks:
        extracted = text[chunk.character_start:chunk.character_end]
        assert extracted == chunk.content


def test_chunking_invalid_parameters():
    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        TextChunker(chunk_size=0)

    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        TextChunker(chunk_size=-10)

    with pytest.raises(ValueError, match="chunk_overlap must be non-negative"):
        TextChunker(chunk_size=100, chunk_overlap=-1)

    with pytest.raises(ValueError, match="strictly less than chunk_size"):
        TextChunker(chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError, match="strictly less than chunk_size"):
        TextChunker(chunk_size=100, chunk_overlap=150)


# ==============================================================================
# 2. Retrieval Tests
# ==============================================================================

@pytest.fixture
def sample_rag_index():
    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    source_a1 = uuid.uuid4()
    source_a2 = uuid.uuid4()
    source_b1 = uuid.uuid4()

    doc_a1 = uuid.uuid4()
    doc_a2 = uuid.uuid4()
    doc_a3 = uuid.uuid4()
    doc_b1 = uuid.uuid4()

    chunks = [
        # Org A, Source A1, Doc A1: Employee handbook
        RetrievalChunk(
            document_id=doc_a1,
            source_id=source_a1,
            organization_id=org_a,
            content="Employee Handbook 2026: Remote work policy requires VPN connection and MFA.",
            metadata={"chapter": 1},
        ),
        RetrievalChunk(
            document_id=doc_a1,
            source_id=source_a1,
            organization_id=org_a,
            content="Employee Handbook 2026: Expense reimbursement submissions must occur within 30 days.",
            metadata={"chapter": 2},
        ),
        # Org A, Source A1, Doc A2: Security guide
        RetrievalChunk(
            document_id=doc_a2,
            source_id=source_a1,
            organization_id=org_a,
            content="Information Security Runbook: Incident response team contacts and escalation paths.",
            metadata={"section": "incident-response"},
        ),
        # Org A, Source A2, Doc A3: Architecture doc
        RetrievalChunk(
            document_id=doc_a3,
            source_id=source_a2,
            organization_id=org_a,
            content="Platform Architecture: Database clustering and tenant isolation mechanisms.",
            metadata={"system": "backend"},
        ),
        # Org B, Source B1, Doc B1: Cross-tenant data with identical keywords
        RetrievalChunk(
            document_id=doc_b1,
            source_id=source_b1,
            organization_id=org_b,
            content="Competitor Handbook: Remote work policy and confidential executive salaries.",
            metadata={"confidential": True},
        ),
    ]

    return {
        "org_a": org_a,
        "org_b": org_b,
        "source_a1": source_a1,
        "source_a2": source_a2,
        "source_b1": source_b1,
        "doc_a1": doc_a1,
        "doc_a2": doc_a2,
        "doc_a3": doc_a3,
        "doc_b1": doc_b1,
        "chunks": chunks,
    }


@pytest.mark.anyio
async def test_retrieval_empty_query(sample_rag_index):
    retriever = MockRetriever(sample_rag_index["chunks"])
    req = RetrievalRequest(
        organization_id=sample_rag_index["org_a"],
        query="",
    )
    result = await retriever.retrieve(req)
    assert result.retrieval_count == 0
    assert result.chunks == []

    req_ws = RetrievalRequest(
        organization_id=sample_rag_index["org_a"],
        query="   \t\n  ",
    )
    result_ws = await retriever.retrieve(req_ws)
    assert result_ws.retrieval_count == 0
    assert result_ws.chunks == []


@pytest.mark.anyio
async def test_retrieval_relevant_lexical_matches(sample_rag_index):
    retriever = MockRetriever(sample_rag_index["chunks"])
    req = RetrievalRequest(
        organization_id=sample_rag_index["org_a"],
        query="remote work policy VPN",
    )
    result = await retriever.retrieve(req)

    assert result.retrieval_count > 0
    top_chunk = result.chunks[0]
    assert "Remote work policy" in top_chunk.content
    assert top_chunk.score > 0.0
    assert top_chunk.organization_id == sample_rag_index["org_a"]


@pytest.mark.anyio
async def test_retrieval_top_k(sample_rag_index):
    retriever = MockRetriever(sample_rag_index["chunks"])
    # "Employee Handbook" matches 2 chunks in Org A
    req = RetrievalRequest(
        organization_id=sample_rag_index["org_a"],
        query="Employee Handbook",
        top_k=1,
    )
    result = await retriever.retrieve(req)

    assert result.retrieval_count == 1
    assert len(result.chunks) == 1


@pytest.mark.anyio
async def test_retrieval_score_ordering(sample_rag_index):
    retriever = MockRetriever(sample_rag_index["chunks"])
    # Query has "Handbook policy VPN" -> Chunk 1 has 3/3 terms, Chunk 2 has 1/3 terms
    req = RetrievalRequest(
        organization_id=sample_rag_index["org_a"],
        query="Handbook policy VPN",
        top_k=5,
    )
    result = await retriever.retrieve(req)

    assert len(result.chunks) >= 2
    for i in range(len(result.chunks) - 1):
        assert result.chunks[i].score >= result.chunks[i + 1].score
    assert result.chunks[0].score > result.chunks[1].score


@pytest.mark.anyio
async def test_retrieval_organization_isolation(sample_rag_index):
    retriever = MockRetriever(sample_rag_index["chunks"])
    # Org B has "confidential executive salaries" and "Remote work policy"
    req_a = RetrievalRequest(
        organization_id=sample_rag_index["org_a"],
        query="confidential salaries remote work policy",
        top_k=10,
    )
    result_a = await retriever.retrieve(req_a)

    # Must NEVER include Org B's chunk
    for chunk in result_a.chunks:
        assert chunk.organization_id == sample_rag_index["org_a"]
        assert "confidential executive salaries" not in chunk.content

    # Querying as Org B gets Org B's chunk
    req_b = RetrievalRequest(
        organization_id=sample_rag_index["org_b"],
        query="confidential salaries",
    )
    result_b = await retriever.retrieve(req_b)
    assert result_b.retrieval_count == 1
    assert result_b.chunks[0].organization_id == sample_rag_index["org_b"]


@pytest.mark.anyio
async def test_retrieval_source_filtering(sample_rag_index):
    retriever = MockRetriever(sample_rag_index["chunks"])
    # Filter only source_a2 (Platform Architecture)
    req = RetrievalRequest(
        organization_id=sample_rag_index["org_a"],
        query="database isolation policy handbook",
        source_ids=[sample_rag_index["source_a2"]],
    )
    result = await retriever.retrieve(req)

    assert result.retrieval_count == 1
    assert result.chunks[0].source_id == sample_rag_index["source_a2"]
    assert "Platform Architecture" in result.chunks[0].content


@pytest.mark.anyio
async def test_retrieval_document_filtering(sample_rag_index):
    retriever = MockRetriever(sample_rag_index["chunks"])
    # Filter only doc_a2 (Security guide)
    req = RetrievalRequest(
        organization_id=sample_rag_index["org_a"],
        query="incident response escalation handbook policy",
        document_ids=[sample_rag_index["doc_a2"]],
    )
    result = await retriever.retrieve(req)

    assert result.retrieval_count == 1
    assert result.chunks[0].document_id == sample_rag_index["doc_a2"]
    assert "Information Security Runbook" in result.chunks[0].content


@pytest.mark.anyio
async def test_retrieval_no_match_behavior(sample_rag_index):
    retriever = MockRetriever(sample_rag_index["chunks"])
    req = RetrievalRequest(
        organization_id=sample_rag_index["org_a"],
        query="quantum cryptography astronaut teleportation",
    )
    result = await retriever.retrieve(req)

    assert result.retrieval_count == 0
    assert result.chunks == []


def test_retriever_index_management():
    retriever = MockRetriever()
    assert len(retriever.chunks) == 0

    chunk1 = RetrievalChunk(
        document_id=uuid.uuid4(),
        source_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        content="Chunk 1",
    )
    chunk2 = RetrievalChunk(
        document_id=uuid.uuid4(),
        source_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        content="Chunk 2",
    )

    retriever.index_chunk(chunk1)
    assert len(retriever.chunks) == 1

    retriever.index_chunks([chunk2])
    assert len(retriever.chunks) == 2

    retriever.clear()
    assert len(retriever.chunks) == 0


# ==============================================================================
# 3. Context Builder Tests
# ==============================================================================

def test_context_builder_empty_retrieval():
    empty_result = RetrievalResult(chunks=[], query="test query", retrieval_count=0)
    context = build_retrieved_context("test query", empty_result)

    assert isinstance(context, RetrievedContext)
    assert context.query == "test query"
    assert context.formatted_context == ""
    assert context.chunks == []
    assert context.sources_used == []
    assert context.documents_used == []
    assert context.total_chunks == 0


def test_context_builder_one_chunk():
    doc_id = uuid.uuid4()
    source_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    chunk = RetrievalChunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        source_id=source_id,
        organization_id=uuid.uuid4(),
        content="Single chunk test content for enterprise RAG.",
        score=0.92,
    )
    result = RetrievalResult(chunks=[chunk], query="What is enterprise RAG?")
    context = ContextBuilder().build("What is enterprise RAG?", result)

    assert context.query == "What is enterprise RAG?"
    assert context.total_chunks == 1
    assert context.sources_used == [source_id]
    assert context.documents_used == [doc_id]
    assert str(chunk_id) in context.formatted_context
    assert str(doc_id) in context.formatted_context
    assert str(source_id) in context.formatted_context
    assert "Single chunk test content for enterprise RAG." in context.formatted_context


def test_context_builder_multiple_chunks_ordering():
    doc1 = uuid.uuid4()
    doc2 = uuid.uuid4()
    source1 = uuid.uuid4()

    c1 = RetrievalChunk(
        document_id=doc1,
        source_id=source1,
        organization_id=uuid.uuid4(),
        content="Primary high-score chunk",
        score=0.95,
    )
    c2 = RetrievalChunk(
        document_id=doc2,
        source_id=source1,
        organization_id=uuid.uuid4(),
        content="Secondary lower-score chunk",
        score=0.60,
    )

    result = RetrievalResult(chunks=[c1, c2], query="multi-chunk query")
    context = build_retrieved_context("multi-chunk query", result)

    assert context.total_chunks == 2
    # Preserves order in list
    assert context.chunks[0].content == "Primary high-score chunk"
    assert context.chunks[1].content == "Secondary lower-score chunk"

    # Preserves order in formatted string
    pos_c1 = context.formatted_context.find("Primary high-score chunk")
    pos_c2 = context.formatted_context.find("Secondary lower-score chunk")
    assert pos_c1 != -1
    assert pos_c2 != -1
    assert pos_c1 < pos_c2


def test_context_builder_metadata_preservation():
    doc_id = uuid.uuid4()
    source_id = uuid.uuid4()
    meta = {"source_file": "runbook.pdf", "page": 42}

    chunk = RetrievalChunk(
        document_id=doc_id,
        source_id=source_id,
        organization_id=uuid.uuid4(),
        content="Metadata preservation test",
        metadata=meta,
        score=0.88,
    )
    result = RetrievalResult(chunks=[chunk], query="meta query")
    context = build_retrieved_context("meta query", result)

    assert context.chunks[0].metadata == meta
    assert context.chunks[0].score == 0.88


def test_context_builder_deterministic_formatting():
    doc_id = uuid.uuid4()
    source_id = uuid.uuid4()

    chunks = [
        RetrievalChunk(
            document_id=doc_id,
            source_id=source_id,
            organization_id=uuid.uuid4(),
            content=f"Determinism test block {i}",
            score=1.0 - (i * 0.1),
        )
        for i in range(3)
    ]
    result = RetrievalResult(chunks=chunks, query="determinism query")

    context_1 = build_retrieved_context("determinism query", result)
    context_2 = build_retrieved_context("determinism query", result)

    assert context_1.formatted_context == context_2.formatted_context
    assert context_1.sources_used == context_2.sources_used
    assert context_1.documents_used == context_2.documents_used

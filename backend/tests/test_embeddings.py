import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.embeddings import (
    BaseEmbeddingProvider,
    EmbeddingBatchRequest,
    EmbeddingBatchResponse,
    EmbeddingConfigurationError,
    EmbeddingError,
    EmbeddingGateway,
    EmbeddingProviderError,
    EmbeddingRequest,
    EmbeddingResponse,
    MockEmbeddingProvider,
    get_embedding_gateway,
)


# ==============================================================================
# 1. Schema Validation Tests
# ==============================================================================

def test_embedding_request_valid():
    req = EmbeddingRequest(input="ORVEX platform architecture", model="text-embed-1", dimensions=128)
    assert req.input == "ORVEX platform architecture"
    assert req.model == "text-embed-1"
    assert req.dimensions == 128


def test_embedding_request_defaults():
    req = EmbeddingRequest(input="Minimal request")
    assert req.input == "Minimal request"
    assert req.model is None
    assert req.dimensions is None


def test_embedding_request_empty_input_rejected():
    with pytest.raises(ValidationError, match="Input text cannot be empty"):
        EmbeddingRequest(input="")

    with pytest.raises(ValidationError, match="Input text cannot be empty"):
        EmbeddingRequest(input="   \n\t  ")


def test_embedding_request_invalid_dimensions():
    with pytest.raises(ValidationError):
        EmbeddingRequest(input="valid text", dimensions=0)

    with pytest.raises(ValidationError):
        EmbeddingRequest(input="valid text", dimensions=-10)


def test_embedding_response_valid():
    resp = EmbeddingResponse(
        embedding=[0.1, -0.2, 0.3],
        dimensions=3,
        model="mock-embedding",
        provider="mock",
    )
    assert resp.dimensions == 3
    assert len(resp.embedding) == 3
    assert resp.model == "mock-embedding"
    assert resp.provider == "mock"


def test_embedding_response_dimension_mismatch_rejected():
    with pytest.raises(ValidationError, match="does not match declared dimensions"):
        EmbeddingResponse(
            embedding=[0.1, 0.2],
            dimensions=3,
            model="mock-embedding",
            provider="mock",
        )


def test_embedding_batch_request_valid():
    batch = EmbeddingBatchRequest(inputs=["doc1 text", "doc2 text"], dimensions=64)
    assert len(batch.inputs) == 2
    assert batch.dimensions == 64


def test_embedding_batch_request_empty_inputs_rejected():
    with pytest.raises(ValidationError):
        EmbeddingBatchRequest(inputs=[])

    with pytest.raises(ValidationError, match="cannot be empty or whitespace-only"):
        EmbeddingBatchRequest(inputs=["valid", "   "])


def test_embedding_batch_response_dimension_mismatch_rejected():
    with pytest.raises(ValidationError, match="does not match declared dimensions"):
        EmbeddingBatchResponse(
            embeddings=[[0.1, 0.2], [0.3]],  # second vector length is 1, expected 2
            dimensions=2,
            model="mock-embedding",
            provider="mock",
            count=2,
        )


# ==============================================================================
# 2. Mock Provider Tests
# ==============================================================================

@pytest.mark.anyio
async def test_mock_provider_deterministic_output():
    provider = MockEmbeddingProvider(default_model="mock-embedding", default_dimensions=64)
    req1 = EmbeddingRequest(input="Enterprise AI Copilot", dimensions=64)
    req2 = EmbeddingRequest(input="Enterprise AI Copilot", dimensions=64)

    resp1 = await provider.embed(req1)
    resp2 = await provider.embed(req2)

    assert resp1.embedding == resp2.embedding
    assert resp1.dimensions == 64
    assert resp1.model == "mock-embedding"
    assert resp1.provider == "mock"


@pytest.mark.anyio
async def test_mock_provider_different_inputs_produce_different_outputs():
    provider = MockEmbeddingProvider()
    resp_a = await provider.embed(EmbeddingRequest(input="Knowledge base document A"))
    resp_b = await provider.embed(EmbeddingRequest(input="Knowledge base document B"))

    assert resp_a.embedding != resp_b.embedding


@pytest.mark.anyio
async def test_mock_provider_dimensions_honored():
    provider = MockEmbeddingProvider()

    for dims in [8, 32, 128, 384, 768]:
        resp = await provider.embed(EmbeddingRequest(input="Dimension scaling test", dimensions=dims))
        assert resp.dimensions == dims
        assert len(resp.embedding) == dims


@pytest.mark.anyio
async def test_mock_provider_bounded_vector_values():
    provider = MockEmbeddingProvider()
    resp = await provider.embed(EmbeddingRequest(input="Bounding check on vector coefficients", dimensions=256))

    for val in resp.embedding:
        assert isinstance(val, float)
        assert -1.0 <= val <= 1.0


@pytest.mark.anyio
async def test_mock_provider_custom_model_preserved():
    provider = MockEmbeddingProvider(default_model="default-embed")
    resp_default = await provider.embed(EmbeddingRequest(input="model test"))
    assert resp_default.model == "default-embed"

    resp_custom = await provider.embed(EmbeddingRequest(input="model test", model="custom-embed-v2"))
    assert resp_custom.model == "custom-embed-v2"


@pytest.mark.anyio
async def test_mock_provider_batch_embedding():
    provider = MockEmbeddingProvider(default_dimensions=32)
    batch_req = EmbeddingBatchRequest(inputs=["Text alpha", "Text beta", "Text gamma"], dimensions=32)

    batch_resp = await provider.embed_batch(batch_req)

    assert batch_resp.count == 3
    assert len(batch_resp.embeddings) == 3
    assert batch_resp.dimensions == 32

    # Each batch item should match the individual embed call
    single_alpha = await provider.embed(EmbeddingRequest(input="Text alpha", dimensions=32))
    single_beta = await provider.embed(EmbeddingRequest(input="Text beta", dimensions=32))
    assert batch_resp.embeddings[0] == single_alpha.embedding
    assert batch_resp.embeddings[1] == single_beta.embedding


# ==============================================================================
# 3. Gateway Tests
# ==============================================================================

@pytest.mark.anyio
async def test_gateway_resolves_mock_provider():
    settings = Settings(EMBEDDING_PROVIDER="mock", EMBEDDING_MODEL="mock-model", EMBEDDING_DIMENSIONS=128)
    gateway = EmbeddingGateway(settings=settings)

    assert isinstance(gateway.provider, MockEmbeddingProvider)
    assert gateway.provider.default_model == "mock-model"
    assert gateway.provider.default_dimensions == 128


@pytest.mark.anyio
async def test_gateway_resolves_test_alias():
    settings = Settings(EMBEDDING_PROVIDER="test", EMBEDDING_MODEL="test-model", EMBEDDING_DIMENSIONS=64)
    gateway = EmbeddingGateway(settings=settings)

    assert isinstance(gateway.provider, MockEmbeddingProvider)
    assert gateway.provider.default_model == "test-model"


def test_gateway_unsupported_provider_raises_configuration_error():
    settings = Settings(EMBEDDING_PROVIDER="nonexistent-provider")
    with pytest.raises(EmbeddingConfigurationError, match="Unsupported embedding provider"):
        EmbeddingGateway(settings=settings)


@pytest.mark.anyio
async def test_gateway_successful_embedding_with_defaults():
    settings = Settings(
        EMBEDDING_PROVIDER="mock",
        EMBEDDING_MODEL="env-default-model",
        EMBEDDING_DIMENSIONS=100,
    )
    gateway = EmbeddingGateway(settings=settings)

    req = EmbeddingRequest(input="Default configuration embedding test")
    resp = await gateway.embed(req)

    assert resp.dimensions == 100
    assert len(resp.embedding) == 100
    assert resp.model == "env-default-model"
    assert resp.provider == "mock"


@pytest.mark.anyio
async def test_gateway_overrides_defaults_when_specified():
    settings = Settings(
        EMBEDDING_PROVIDER="mock",
        EMBEDDING_MODEL="env-default-model",
        EMBEDDING_DIMENSIONS=100,
    )
    gateway = EmbeddingGateway(settings=settings)

    req = EmbeddingRequest(
        input="Override test",
        model="custom-override-model",
        dimensions=50,
    )
    resp = await gateway.embed(req)

    assert resp.dimensions == 50
    assert len(resp.embedding) == 50
    assert resp.model == "custom-override-model"


@pytest.mark.anyio
async def test_gateway_successful_batch_embedding():
    settings = Settings(EMBEDDING_PROVIDER="mock", EMBEDDING_DIMENSIONS=48)
    gateway = EmbeddingGateway(settings=settings)

    batch_req = EmbeddingBatchRequest(inputs=["Batch item 1", "Batch item 2"])
    batch_resp = await gateway.embed_batch(batch_req)

    assert batch_resp.count == 2
    assert batch_resp.dimensions == 48
    assert len(batch_resp.embeddings) == 2


@pytest.mark.anyio
async def test_gateway_normalizes_unexpected_provider_failure():
    class FailingProvider(BaseEmbeddingProvider):
        async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
            raise RuntimeError("Underlying driver crashed")

    gateway = EmbeddingGateway(provider=FailingProvider())
    with pytest.raises(EmbeddingProviderError, match="Embedding could not be generated"):
        await gateway.embed(EmbeddingRequest(input="Will fail"))


@pytest.mark.anyio
async def test_gateway_normalizes_unexpected_batch_failure():
    class FailingBatchProvider(BaseEmbeddingProvider):
        async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
            raise RuntimeError("Embed failed")

        async def embed_batch(self, request: EmbeddingBatchRequest) -> EmbeddingBatchResponse:
            raise ConnectionResetError("Socket broken")

    gateway = EmbeddingGateway(provider=FailingBatchProvider())
    with pytest.raises(EmbeddingProviderError, match="Batch embeddings could not be generated"):
        await gateway.embed_batch(EmbeddingBatchRequest(inputs=["Item 1"]))


@pytest.mark.anyio
async def test_gateway_propagates_existing_embedding_error():
    class CustomErrorProvider(BaseEmbeddingProvider):
        async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
            raise EmbeddingConfigurationError("Custom configuration problem")

    gateway = EmbeddingGateway(provider=CustomErrorProvider())
    with pytest.raises(EmbeddingConfigurationError, match="Custom configuration problem"):
        await gateway.embed(EmbeddingRequest(input="Propagate error"))


def test_get_embedding_gateway_factory():
    gw = get_embedding_gateway()
    assert isinstance(gw, EmbeddingGateway)
    assert isinstance(gw.provider, MockEmbeddingProvider)

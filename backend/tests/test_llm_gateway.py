import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.llm.errors import (
    ConfigurationError,
    LLMError,
    ProviderRequestError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)
from app.llm.gateway import LLMGateway, get_llm_gateway
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.openai import OpenAIProvider
from app.llm.schemas import LLMMessage, LLMRequest, LLMResponse, LLMUsage


# ==========================================
# Schema & Contract Unit Tests
# ==========================================

def test_llm_message_validation():
    # Valid roles
    m_user = LLMMessage(role="user", content="Hello")
    assert m_user.role == "user"
    assert m_user.content == "Hello"

    m_system = LLMMessage(role="system", content="Act as enterprise assistant")
    assert m_system.role == "system"

    m_asst = LLMMessage(role="assistant", content="How may I assist?")
    assert m_asst.role == "assistant"

    # Role normalized to lowercase
    m_upper = LLMMessage(role="USER", content="uppercase role")
    assert m_upper.role == "user"

    # Invalid role
    with pytest.raises(ValidationError):
        LLMMessage(role="tool", content="unsupported role")

    # Blank content
    with pytest.raises(ValidationError):
        LLMMessage(role="user", content="   ")


def test_llm_request_normalization():
    req = LLMRequest(
        messages=[LLMMessage(role="user", content="Test query")],
        system_instruction="Be concise",
        model="gpt-4o",
        temperature=0.5,
        max_tokens=500,
    )
    assert len(req.messages) == 1
    assert req.system_instruction == "Be concise"
    assert req.model == "gpt-4o"
    assert req.temperature == 0.5
    assert req.max_tokens == 500

    # Empty messages rejected
    with pytest.raises(ValidationError):
        LLMRequest(messages=[])


def test_llm_usage_computation():
    usage = LLMUsage(input_tokens=10, output_tokens=25, total_tokens=35)
    assert usage.input_tokens == 10
    assert usage.output_tokens == 25
    assert usage.total_tokens == 35


# ==========================================
# Mock Provider Tests
# ==========================================

@pytest.mark.anyio
async def test_mock_provider_generation():
    provider = MockLLMProvider(default_model="mock-model", simulated_latency_ms=1)
    req = LLMRequest(
        messages=[LLMMessage(role="user", content="What is ORVEX?")],
        system_instruction="You are ORVEX AI",
    )
    resp = await provider.generate(req)

    assert isinstance(resp, LLMResponse)
    assert resp.provider == "mock"
    assert resp.model == "mock-model"
    assert "ORVEX Assistant response to: 'What is ORVEX?'" in resp.content
    assert resp.usage.input_tokens > 0
    assert resp.usage.output_tokens > 0
    assert resp.usage.total_tokens == resp.usage.input_tokens + resp.usage.output_tokens
    assert resp.finish_reason == "stop"
    assert resp.latency_ms >= 0


@pytest.mark.anyio
async def test_mock_provider_custom_canned_response():
    provider = MockLLMProvider(default_response="Custom canned enterprise output")
    req = LLMRequest(messages=[LLMMessage(role="user", content="Any query")])
    resp = await provider.generate(req)
    assert resp.content == "Custom canned enterprise output"


# ==========================================
# LLM Gateway Lifecycle & Resolution Tests
# ==========================================

@pytest.mark.anyio
async def test_llm_gateway_resolution_mock():
    custom_settings = Settings(LLM_PROVIDER="mock", LLM_MODEL="test-mock-model")
    gateway = LLMGateway(settings=custom_settings)

    meta = gateway.get_metadata()
    assert meta.name == "mock"
    assert meta.default_model == "test-mock-model"

    req = LLMRequest(messages=[LLMMessage(role="user", content="Ping")])
    resp = await gateway.generate(req)
    assert resp.provider == "mock"
    assert resp.model == "test-mock-model"


@pytest.mark.anyio
async def test_llm_gateway_resolution_openai():
    custom_settings = Settings(
        LLM_PROVIDER="openai",
        LLM_MODEL="gpt-4o-mini",
        LLM_API_KEY="sk-test-fake-key",
    )
    gateway = LLMGateway(settings=custom_settings)
    meta = gateway.get_metadata()
    assert meta.name == "openai"
    assert meta.default_model == "gpt-4o-mini"


@pytest.mark.anyio
async def test_llm_gateway_resolution_claude():
    custom_settings = Settings(
        LLM_PROVIDER="claude",
        LLM_MODEL="claude-3-7-sonnet-20250219",
        ANTHROPIC_API_KEY="sk-ant-test-key",
    )
    gateway = LLMGateway(settings=custom_settings)
    meta = gateway.get_metadata()
    assert meta.name == "claude"
    assert meta.default_model == "claude-3-7-sonnet-20250219"


@pytest.mark.anyio
async def test_llm_gateway_resolution_claude_fallback_llm_api_key():
    custom_settings = Settings(
        LLM_PROVIDER="anthropic",
        LLM_MODEL="claude-3-5-haiku-20241022",
        LLM_API_KEY="sk-ant-generic-key",
    )
    gateway = LLMGateway(settings=custom_settings)
    meta = gateway.get_metadata()
    assert meta.name == "claude"
    assert meta.default_model == "claude-3-5-haiku-20241022"


def test_llm_gateway_unsupported_provider():
    custom_settings = Settings(LLM_PROVIDER="unsupported_vendor_xyz")
    with pytest.raises(ConfigurationError) as exc_info:
        LLMGateway(settings=custom_settings)
    assert "Unsupported LLM provider" in exc_info.value.detail


# ==========================================
# OpenAI Provider Unit & Error Mapping Tests
# ==========================================

@pytest.mark.anyio
async def test_openai_missing_api_key_raises_configuration_error():
    provider = OpenAIProvider(api_key=None, base_url="https://api.openai.com/v1")
    req = LLMRequest(messages=[LLMMessage(role="user", content="Hello")])

    with pytest.raises(ConfigurationError) as exc_info:
        await provider.generate(req)
    assert exc_info.value.status_code == 500
    assert "invalid or missing credentials" in exc_info.value.detail.lower()


@pytest.mark.anyio
async def test_openai_local_endpoint_allows_empty_api_key():
    # Local endpoints (Ollama/vLLM) should not fail on missing api_key
    mock_transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code=200,
            json={
                "choices": [{"message": {"content": "Local model output"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 15, "completion_tokens": 5, "total_tokens": 20},
                "model": "llama3",
            },
        )
    )
    async with httpx.AsyncClient(transport=mock_transport) as client:
        provider = OpenAIProvider(
            api_key=None,
            base_url="http://localhost:11434/v1",
            default_model="llama3",
            client=client,
        )
        req = LLMRequest(messages=[LLMMessage(role="user", content="Hello")])
        resp = await provider.generate(req)
        assert resp.content == "Local model output"
        assert resp.model == "llama3"


@pytest.mark.anyio
async def test_openai_successful_generation():
    fake_api_key = "sk-mock-secret-key-12345"
    captured_auth = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_auth.append(request.headers.get("authorization"))
        return httpx.Response(
            status_code=200,
            json={
                "id": "chatcmpl-test-123",
                "object": "chat.completion",
                "model": "gpt-4o-mini",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "Real model generated response."},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
        provider = OpenAIProvider(api_key=fake_api_key, client=client)
        req = LLMRequest(
            messages=[LLMMessage(role="user", content="Tell me about ORVEX.")],
            system_instruction="Be helpful",
        )
        resp = await provider.generate(req)

        assert resp.content == "Real model generated response."
        assert resp.model == "gpt-4o-mini"
        assert resp.provider == "openai"
        assert resp.usage.input_tokens == 20
        assert resp.usage.output_tokens == 10
        assert resp.usage.total_tokens == 30
        assert captured_auth[0] == f"Bearer {fake_api_key}"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "status_code,expected_error_type",
    [
        (401, ConfigurationError),
        (403, ConfigurationError),
        (429, RateLimitError),
        (400, ProviderRequestError),
        (422, ProviderRequestError),
        (500, ProviderUnavailableError),
        (502, ProviderUnavailableError),
        (503, ProviderUnavailableError),
    ],
)
async def test_openai_http_error_mapping(status_code, expected_error_type):
    mock_transport = httpx.MockTransport(
        lambda req: httpx.Response(status_code=status_code, json={"error": "provider failure"})
    )
    async with httpx.AsyncClient(transport=mock_transport) as client:
        provider = OpenAIProvider(api_key="sk-test", client=client)
        req = LLMRequest(messages=[LLMMessage(role="user", content="test")])

        with pytest.raises(expected_error_type) as exc_info:
            await provider.generate(req)

        # Assert no sensitive key is leaked in detail
        assert "sk-test" not in exc_info.value.detail


@pytest.mark.anyio
async def test_openai_timeout_handling():
    def timeout_handler(request: httpx.Request):
        raise httpx.ReadTimeout("Connection timed out", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(timeout_handler)) as client:
        provider = OpenAIProvider(api_key="sk-test", client=client)
        req = LLMRequest(messages=[LLMMessage(role="user", content="test")])

        with pytest.raises(ProviderTimeoutError) as exc_info:
            await provider.generate(req)
        assert exc_info.value.status_code == 504
        assert "timed out" in exc_info.value.detail.lower()

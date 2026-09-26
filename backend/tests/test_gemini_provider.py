import httpx
import pytest

from app.core.config import Settings
from app.llm.errors import (
    ConfigurationError,
    ProviderRequestError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)
from app.llm.gateway import DEFAULT_GEMINI_BASE_URL, DEFAULT_GEMINI_MODEL, LLMGateway
from app.llm.providers.openai import OpenAIProvider
from app.llm.schemas import LLMMessage, LLMRequest, LLMResponse


# ==========================================
# Gemini Provider Resolution Tests
# ==========================================

@pytest.mark.anyio
async def test_gemini_provider_resolution():
    custom_settings = Settings(
        LLM_PROVIDER="gemini",
        GEMINI_API_KEY="sk-gemini-test-secret",
    )
    gateway = LLMGateway(settings=custom_settings)
    meta = gateway.get_metadata()
    assert meta.name == "gemini"
    assert meta.default_model == DEFAULT_GEMINI_MODEL


@pytest.mark.anyio
async def test_gemini_provider_resolution_custom_model():
    custom_settings = Settings(
        LLM_PROVIDER="gemini",
        LLM_MODEL="gemini-2.0-flash",
        GEMINI_API_KEY="sk-gemini-test-secret",
    )
    gateway = LLMGateway(settings=custom_settings)
    meta = gateway.get_metadata()
    assert meta.name == "gemini"
    assert meta.default_model == "gemini-2.0-flash"


@pytest.mark.anyio
async def test_gemini_provider_resolution_google_alias():
    custom_settings = Settings(
        LLM_PROVIDER="google",
        GEMINI_API_KEY="sk-gemini-alias-key",
    )
    gateway = LLMGateway(settings=custom_settings)
    meta = gateway.get_metadata()
    assert meta.name == "gemini"


@pytest.mark.anyio
async def test_gemini_provider_resolution_fallback_llm_api_key():
    custom_settings = Settings(
        LLM_PROVIDER="gemini",
        LLM_API_KEY="sk-generic-fallback-key",
    )
    gateway = LLMGateway(settings=custom_settings)
    meta = gateway.get_metadata()
    assert meta.name == "gemini"


# ==========================================
# Gemini Transport & Generation Tests
# ==========================================

@pytest.mark.anyio
async def test_gemini_successful_generation():
    fake_api_key = "sk-gemini-secret-test-key"
    captured_request = {}

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_request["url"] = str(request.url)
        captured_request["headers"] = dict(request.headers)
        captured_request["body"] = request.read().decode("utf-8")
        return httpx.Response(
            status_code=200,
            json={
                "id": "chatcmpl-gemini-12345",
                "object": "chat.completion",
                "model": "gemini-3-flash-preview",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Gemini response generated via OpenAI-compatible endpoint.",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 14,
                    "completion_tokens": 22,
                    "total_tokens": 36,
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
        provider = OpenAIProvider(
            api_key=fake_api_key,
            base_url=DEFAULT_GEMINI_BASE_URL,
            default_model="gemini-3-flash-preview",
            client=client,
            provider_name="gemini",
        )
        req = LLMRequest(
            messages=[LLMMessage(role="user", content="Explain quantum computing")],
            system_instruction="Be concise.",
            temperature=0.7,
            max_tokens=2048,
        )
        resp = await provider.generate(req)

        assert isinstance(resp, LLMResponse)
        assert resp.content == "Gemini response generated via OpenAI-compatible endpoint."
        assert resp.model == "gemini-3-flash-preview"
        assert resp.provider == "gemini"
        assert resp.usage.input_tokens == 14
        assert resp.usage.output_tokens == 22
        assert resp.usage.total_tokens == 36
        assert resp.finish_reason == "stop"
        assert resp.latency_ms >= 0

        # Verify Google OpenAI-compatible endpoint and authentication header
        assert captured_request["url"] == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        assert captured_request["headers"]["authorization"] == f"Bearer {fake_api_key}"
        assert "application/json" in captured_request["headers"]["content-type"]


@pytest.mark.anyio
async def test_gemini_model_selection_override():
    captured_payload = {}

    def mock_handler(request: httpx.Request) -> httpx.Response:
        import json
        captured_payload.update(json.loads(request.read()))
        return httpx.Response(
            status_code=200,
            json={
                "model": "gemini-2.0-flash",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "Flash 2.0 output."},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
        provider = OpenAIProvider(
            api_key="sk-gemini-test",
            base_url=DEFAULT_GEMINI_BASE_URL,
            default_model="gemini-3-flash-preview",
            client=client,
            provider_name="gemini",
        )
        req = LLMRequest(
            messages=[LLMMessage(role="user", content="Ping")],
            model="gemini-2.0-flash",
        )
        resp = await provider.generate(req)

        assert captured_payload["model"] == "gemini-2.0-flash"
        assert resp.model == "gemini-2.0-flash"


@pytest.mark.anyio
async def test_gemini_missing_api_key_raises_configuration_error():
    provider = OpenAIProvider(
        api_key=None,
        base_url=DEFAULT_GEMINI_BASE_URL,
        default_model="gemini-3-flash-preview",
        provider_name="gemini",
    )
    req = LLMRequest(messages=[LLMMessage(role="user", content="Hello")])

    with pytest.raises(ConfigurationError) as exc_info:
        await provider.generate(req)
    assert exc_info.value.status_code == 500
    assert "missing credentials" in exc_info.value.detail.lower()
    assert "GEMINI_API_KEY" in exc_info.value.internal_error


@pytest.mark.anyio
async def test_gemini_timeout_handling():
    def timeout_handler(request: httpx.Request):
        raise httpx.ReadTimeout("Gemini connection timed out", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(timeout_handler)) as client:
        provider = OpenAIProvider(
            api_key="sk-gemini-test",
            base_url=DEFAULT_GEMINI_BASE_URL,
            default_model="gemini-3-flash-preview",
            client=client,
            provider_name="gemini",
        )
        req = LLMRequest(messages=[LLMMessage(role="user", content="test")])

        with pytest.raises(ProviderTimeoutError) as exc_info:
            await provider.generate(req)
        assert exc_info.value.status_code == 504
        assert "timed out" in exc_info.value.detail.lower()


@pytest.mark.anyio
async def test_gemini_connection_error_handling():
    def connect_handler(request: httpx.Request):
        raise httpx.ConnectError("Connection refused by Gemini API", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(connect_handler)) as client:
        provider = OpenAIProvider(
            api_key="sk-gemini-test",
            base_url=DEFAULT_GEMINI_BASE_URL,
            default_model="gemini-3-flash-preview",
            client=client,
            provider_name="gemini",
        )
        req = LLMRequest(messages=[LLMMessage(role="user", content="test")])

        with pytest.raises(ProviderUnavailableError) as exc_info:
            await provider.generate(req)
        assert exc_info.value.status_code == 503
        assert "unavailable" in exc_info.value.detail.lower()


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
async def test_gemini_http_error_mapping(status_code, expected_error_type):
    secret_key = "sk-gemini-secret-do-not-leak"
    mock_transport = httpx.MockTransport(
        lambda req: httpx.Response(
            status_code=status_code,
            json={"error": {"message": "Gemini error", "code": status_code}},
        )
    )
    async with httpx.AsyncClient(transport=mock_transport) as client:
        provider = OpenAIProvider(
            api_key=secret_key,
            base_url=DEFAULT_GEMINI_BASE_URL,
            default_model="gemini-3-flash-preview",
            client=client,
            provider_name="gemini",
        )
        req = LLMRequest(messages=[LLMMessage(role="user", content="test")])

        with pytest.raises(expected_error_type) as exc_info:
            await provider.generate(req)

        # Assert no sensitive key is leaked in detail
        assert secret_key not in exc_info.value.detail


@pytest.mark.anyio
async def test_gemini_malformed_response_handling():
    mock_transport = httpx.MockTransport(
        lambda req: httpx.Response(status_code=200, json={"choices": []})
    )
    async with httpx.AsyncClient(transport=mock_transport) as client:
        provider = OpenAIProvider(
            api_key="sk-gemini-test",
            base_url=DEFAULT_GEMINI_BASE_URL,
            default_model="gemini-3-flash-preview",
            client=client,
            provider_name="gemini",
        )
        req = LLMRequest(messages=[LLMMessage(role="user", content="test")])

        with pytest.raises(ProviderRequestError) as exc_info:
            await provider.generate(req)
        assert "empty completion response" in exc_info.value.detail.lower()


@pytest.mark.anyio
async def test_gemini_metadata():
    provider = OpenAIProvider(
        api_key="sk-gemini-test",
        base_url=DEFAULT_GEMINI_BASE_URL,
        default_model="gemini-3-flash-preview",
        provider_name="gemini",
    )
    meta = provider.get_metadata()
    assert meta.name == "gemini"
    assert meta.default_model == "gemini-3-flash-preview"
    assert "gemini-3-flash-preview" in meta.supported_models

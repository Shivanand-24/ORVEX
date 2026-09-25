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
from app.llm.gateway import LLMGateway
from app.llm.providers.claude import ClaudeProvider
from app.llm.schemas import LLMMessage, LLMRequest, LLMResponse


# ==========================================
# Claude Provider Unit & Transport Tests
# ==========================================

@pytest.mark.anyio
async def test_claude_successful_generation():
    fake_api_key = "sk-ant-secret-key-12345"
    captured_request = {}

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_request["headers"] = dict(request.headers)
        captured_request["body"] = request.read().decode("utf-8")
        return httpx.Response(
            status_code=200,
            json={
                "id": "msg_01X9mock",
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Claude generated response for ORVEX."}
                ],
                "model": "claude-3-7-sonnet-20250219",
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": 25,
                    "output_tokens": 15,
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
        provider = ClaudeProvider(
            api_key=fake_api_key,
            default_model="claude-3-7-sonnet-20250219",
            client=client,
        )
        req = LLMRequest(
            messages=[LLMMessage(role="user", content="Tell me about ORVEX.")],
            system_instruction="You are an enterprise AI assistant.",
            temperature=0.5,
            max_tokens=1024,
        )
        resp = await provider.generate(req)

        assert isinstance(resp, LLMResponse)
        assert resp.content == "Claude generated response for ORVEX."
        assert resp.model == "claude-3-7-sonnet-20250219"
        assert resp.provider == "claude"
        assert resp.usage.input_tokens == 25
        assert resp.usage.output_tokens == 15
        assert resp.usage.total_tokens == 40
        assert resp.finish_reason == "end_turn"
        assert resp.latency_ms >= 0

        # Verify headers
        assert captured_request["headers"]["x-api-key"] == fake_api_key
        assert captured_request["headers"]["anthropic-version"] == "2023-06-01"
        assert "application/json" in captured_request["headers"]["content-type"]


@pytest.mark.anyio
async def test_claude_system_prompt_mapping():
    captured_payload = {}

    def mock_handler(request: httpx.Request) -> httpx.Response:
        import json
        captured_payload.update(json.loads(request.read()))
        return httpx.Response(
            status_code=200,
            json={
                "id": "msg_system",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "Acknowledged."}],
                "model": "claude-test",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 10, "output_tokens": 2},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
        provider = ClaudeProvider(api_key="sk-ant-test", default_model="claude-test", client=client)
        req = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
            system_instruction="Strict system directive",
        )
        await provider.generate(req)

        # In Claude API, system prompt is top-level
        assert captured_payload["system"] == "Strict system directive"
        assert len(captured_payload["messages"]) == 1
        assert captured_payload["messages"][0] == {"role": "user", "content": "Hello"}


@pytest.mark.anyio
async def test_claude_system_message_in_history_hoisted():
    captured_payload = {}

    def mock_handler(request: httpx.Request) -> httpx.Response:
        import json
        captured_payload.update(json.loads(request.read()))
        return httpx.Response(
            status_code=200,
            json={
                "content": [{"type": "text", "text": "Response."}],
                "model": "claude-test",
                "usage": {"input_tokens": 10, "output_tokens": 2},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
        provider = ClaudeProvider(api_key="sk-ant-test", default_model="claude-test", client=client)
        req = LLMRequest(
            messages=[
                LLMMessage(role="system", content="Hoisted instruction"),
                LLMMessage(role="user", content="Query"),
            ],
            system_instruction="Top-level prompt",
        )
        await provider.generate(req)

        # Both top-level and hoisted system messages should be merged in system
        assert "Top-level prompt" in captured_payload["system"]
        assert "Hoisted instruction" in captured_payload["system"]
        # No 'system' role inside the messages array
        assert all(m["role"] in ("user", "assistant") for m in captured_payload["messages"])


@pytest.mark.anyio
async def test_claude_multi_turn_history_mapping():
    captured_payload = {}

    def mock_handler(request: httpx.Request) -> httpx.Response:
        import json
        captured_payload.update(json.loads(request.read()))
        return httpx.Response(
            status_code=200,
            json={
                "content": [{"type": "text", "text": "Turn 3 answer."}],
                "model": "claude-test",
                "usage": {"input_tokens": 30, "output_tokens": 10},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
        provider = ClaudeProvider(api_key="sk-ant-test", default_model="claude-test", client=client)
        req = LLMRequest(
            messages=[
                LLMMessage(role="user", content="Question 1"),
                LLMMessage(role="assistant", content="Answer 1"),
                LLMMessage(role="user", content="Question 2"),
            ]
        )
        await provider.generate(req)

        assert len(captured_payload["messages"]) == 3
        assert captured_payload["messages"][0] == {"role": "user", "content": "Question 1"}
        assert captured_payload["messages"][1] == {"role": "assistant", "content": "Answer 1"}
        assert captured_payload["messages"][2] == {"role": "user", "content": "Question 2"}


@pytest.mark.anyio
async def test_claude_multiple_content_blocks_text_extraction():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "content": [
                    {"type": "text", "text": "Part 1: Initial thought. "},
                    {"type": "text", "text": "Part 2: Final conclusion."},
                ],
                "model": "claude-test",
                "usage": {"input_tokens": 10, "output_tokens": 20},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
        provider = ClaudeProvider(api_key="sk-ant-test", default_model="claude-test", client=client)
        req = LLMRequest(messages=[LLMMessage(role="user", content="Explain")])
        resp = await provider.generate(req)

        assert resp.content == "Part 1: Initial thought. Part 2: Final conclusion."


@pytest.mark.anyio
async def test_claude_token_usage_extraction():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "content": [{"type": "text", "text": "Test"}],
                "model": "claude-test",
                "usage": {
                    "input_tokens": 128,
                    "output_tokens": 64,
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
        provider = ClaudeProvider(api_key="sk-ant-test", default_model="claude-test", client=client)
        req = LLMRequest(messages=[LLMMessage(role="user", content="Hi")])
        resp = await provider.generate(req)

        assert resp.usage.input_tokens == 128
        assert resp.usage.output_tokens == 64
        assert resp.usage.total_tokens == 192


@pytest.mark.anyio
async def test_claude_timeout_handling():
    def timeout_handler(request: httpx.Request):
        raise httpx.ReadTimeout("Request timed out", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(timeout_handler)) as client:
        provider = ClaudeProvider(api_key="sk-ant-test", default_model="claude-test", client=client)
        req = LLMRequest(messages=[LLMMessage(role="user", content="Timeout query")])

        with pytest.raises(ProviderTimeoutError) as exc_info:
            await provider.generate(req)
        assert exc_info.value.status_code == 504
        assert "timed out" in exc_info.value.detail.lower()


@pytest.mark.anyio
async def test_claude_connection_error_handling():
    def connect_handler(request: httpx.Request):
        raise httpx.ConnectError("Failed to connect", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(connect_handler)) as client:
        provider = ClaudeProvider(api_key="sk-ant-test", default_model="claude-test", client=client)
        req = LLMRequest(messages=[LLMMessage(role="user", content="Connect query")])

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
async def test_claude_http_error_mapping(status_code, expected_error_type):
    secret_key = "sk-ant-secret-to-never-leak"
    mock_transport = httpx.MockTransport(
        lambda req: httpx.Response(
            status_code=status_code,
            json={"type": "error", "error": {"type": "invalid_request_error", "message": "Failure"}},
        )
    )
    async with httpx.AsyncClient(transport=mock_transport) as client:
        provider = ClaudeProvider(api_key=secret_key, default_model="claude-test", client=client)
        req = LLMRequest(messages=[LLMMessage(role="user", content="test")])

        with pytest.raises(expected_error_type) as exc_info:
            await provider.generate(req)

        # Assert no sensitive key is leaked in detail
        assert secret_key not in exc_info.value.detail


@pytest.mark.anyio
async def test_claude_malformed_response_handling():
    # Empty content blocks
    mock_transport = httpx.MockTransport(
        lambda req: httpx.Response(status_code=200, json={"content": []})
    )
    async with httpx.AsyncClient(transport=mock_transport) as client:
        provider = ClaudeProvider(api_key="sk-ant-test", default_model="claude-test", client=client)
        req = LLMRequest(messages=[LLMMessage(role="user", content="test")])

        with pytest.raises(ProviderRequestError) as exc_info:
            await provider.generate(req)
        assert "empty completion response" in exc_info.value.detail.lower()


@pytest.mark.anyio
async def test_claude_missing_api_key_raises_configuration_error():
    provider = ClaudeProvider(api_key=None, default_model="claude-test")
    req = LLMRequest(messages=[LLMMessage(role="user", content="test")])

    with pytest.raises(ConfigurationError) as exc_info:
        await provider.generate(req)
    assert exc_info.value.status_code == 500
    assert "missing credentials" in exc_info.value.detail.lower()


@pytest.mark.anyio
async def test_claude_missing_model_raises_configuration_error():
    provider = ClaudeProvider(api_key="sk-ant-test", default_model=None)
    req = LLMRequest(messages=[LLMMessage(role="user", content="test")], model=None)

    with pytest.raises(ConfigurationError) as exc_info:
        await provider.generate(req)
    assert exc_info.value.status_code == 500
    assert "missing model" in exc_info.value.detail.lower()


@pytest.mark.anyio
async def test_claude_metadata():
    provider = ClaudeProvider(api_key="sk-ant-test", default_model="my-custom-model")
    meta = provider.get_metadata()
    assert meta.name == "claude"
    assert meta.default_model == "my-custom-model"
    assert "my-custom-model" in meta.supported_models

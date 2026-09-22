import uuid
import pytest
from fastapi.testclient import TestClient

from app.llm.errors import RateLimitError
from app.llm.gateway import LLMGateway, get_llm_gateway
from app.llm.interfaces import BaseLLMProvider
from app.llm.schemas import LLMRequest, LLMResponse, ProviderMetadata
from app.main import app


# ==========================================
# Fixtures
# ==========================================

@pytest.fixture
def setup_chat_conversation(client: TestClient):
    org = client.post("/api/v1/organizations", json={"name": "Chat Org", "slug": f"chat-org-{uuid.uuid4().hex[:6]}"}).json()
    org_id = org["id"]

    user = client.post("/api/v1/users", json={"email": f"chat-{uuid.uuid4().hex[:6]}@orvex.com", "full_name": "Chat User"}).json()
    user_id = user["id"]

    conv = client.post(
        "/api/v1/assistant/conversations",
        json={"organization_id": org_id, "user_id": user_id, "title": "Chat Integration Session"},
    ).json()

    return {"org_id": org_id, "user_id": user_id, "conv_id": conv["id"]}


# ==========================================
# Assistant Chat Integration Tests
# ==========================================

@pytest.mark.anyio
async def test_assistant_chat_turn_success(client: TestClient, setup_chat_conversation):
    conv_id = setup_chat_conversation["conv_id"]
    org_id = setup_chat_conversation["org_id"]

    payload = {
        "content": "What capabilities does ORVEX have?",
    }
    res = client.post(f"/api/v1/assistant/conversations/{conv_id}/chat?organization_id={org_id}", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["conversation_id"] == conv_id
    assert data["provider"] == "mock"
    assert data["model"] == "gpt-4o-mini"
    assert data["user_message"]["role"] == "user"
    assert data["user_message"]["content"] == "What capabilities does ORVEX have?"
    assert data["assistant_message"]["role"] == "assistant"
    assert "ORVEX Assistant response to: 'What capabilities does ORVEX have?'" in data["assistant_message"]["content"]
    assert data["assistant_message"]["tokens_used"] > 0
    assert data["assistant_message"]["latency_ms"] >= 0

    # Verify both messages are persisted in conversation history
    list_res = client.get(f"/api/v1/assistant/conversations/{conv_id}/messages?organization_id={org_id}")
    assert list_res.status_code == 200
    messages = list_res.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


@pytest.mark.anyio
async def test_assistant_chat_multi_turn_history(client: TestClient, setup_chat_conversation):
    conv_id = setup_chat_conversation["conv_id"]

    # Turn 1
    res1 = client.post(f"/api/v1/assistant/conversations/{conv_id}/chat", json={"content": "Turn 1"})
    assert res1.status_code == 200

    # Turn 2
    res2 = client.post(f"/api/v1/assistant/conversations/{conv_id}/chat", json={"content": "Turn 2"})
    assert res2.status_code == 200

    # Turn 3
    res3 = client.post(f"/api/v1/assistant/conversations/{conv_id}/chat", json={"content": "Turn 3"})
    assert res3.status_code == 200

    # Check that 6 total messages exist chronologically
    list_res = client.get(f"/api/v1/assistant/conversations/{conv_id}/messages")
    assert list_res.status_code == 200
    messages = list_res.json()
    assert len(messages) == 6
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant", "user", "assistant"]


@pytest.mark.anyio
async def test_assistant_chat_model_and_system_override(client: TestClient, setup_chat_conversation):
    conv_id = setup_chat_conversation["conv_id"]

    payload = {
        "content": "Analyze compliance regulations",
        "system_instruction": "You are a senior compliance officer.",
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_tokens": 1000,
    }
    res = client.post(f"/api/v1/assistant/conversations/{conv_id}/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["model"] == "gpt-4o"


@pytest.mark.anyio
async def test_assistant_chat_blank_prompt_rejected(client: TestClient, setup_chat_conversation):
    conv_id = setup_chat_conversation["conv_id"]

    res = client.post(f"/api/v1/assistant/conversations/{conv_id}/chat", json={"content": "   "})
    assert res.status_code in (400, 422)


@pytest.mark.anyio
async def test_assistant_chat_conversation_not_found(client: TestClient):
    random_conv_id = str(uuid.uuid4())
    res = client.post(f"/api/v1/assistant/conversations/{random_conv_id}/chat", json={"content": "Hello"})
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_assistant_chat_tenant_isolation(client: TestClient, setup_chat_conversation):
    conv_id = setup_chat_conversation["conv_id"]

    # Create another organization
    org2 = client.post("/api/v1/organizations", json={"name": "Other Org", "slug": f"other-org-{uuid.uuid4().hex[:6]}"}).json()
    org2_id = org2["id"]

    # Calling chat with Org 2 scope on Org 1 conversation must 404
    res = client.post(f"/api/v1/assistant/conversations/{conv_id}/chat?organization_id={org2_id}", json={"content": "Infiltrate"})
    assert res.status_code == 404


@pytest.mark.anyio
async def test_assistant_chat_provider_failure_persists_user_message_only(client: TestClient, setup_chat_conversation):
    conv_id = setup_chat_conversation["conv_id"]

    # Create a failing provider
    class FailingProvider(BaseLLMProvider):
        async def generate(self, request: LLMRequest) -> LLMResponse:
            raise RateLimitError(detail="AI service rate limit exceeded. Please retry shortly.")

        def get_metadata(self) -> ProviderMetadata:
            return ProviderMetadata(name="failing", default_model="failing-model")

    failing_gateway = LLMGateway(provider=FailingProvider())
    app.dependency_overrides[get_llm_gateway] = lambda: failing_gateway

    try:
        res = client.post(f"/api/v1/assistant/conversations/{conv_id}/chat", json={"content": "This prompt is saved in Tx 1"})
        assert res.status_code == 429
        assert "rate limit exceeded" in res.json()["detail"].lower()

        # Verify Transaction 1 persisted user message, but Transaction 2 never created an assistant message
        list_res = client.get(f"/api/v1/assistant/conversations/{conv_id}/messages")
        assert list_res.status_code == 200
        messages = list_res.json()
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "This prompt is saved in Tx 1"
    finally:
        app.dependency_overrides.pop(get_llm_gateway, None)

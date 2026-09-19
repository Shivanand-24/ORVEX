import uuid
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def setup_org_and_user(client: TestClient):
    org_res = client.post("/api/v1/organizations", json={"name": "Assistant Org", "slug": "assistant-org"})
    org_id = org_res.json()["id"]

    user_res = client.post("/api/v1/users", json={"email": "assistant_user@orvex.com", "full_name": "Assistant Tester"})
    user_id = user_res.json()["id"]

    return {"org_id": org_id, "user_id": user_id}


# ==========================================
# Conversation Tests
# ==========================================

@pytest.mark.anyio
async def test_create_conversation_success(client: TestClient, setup_org_and_user):
    org_id = setup_org_and_user["org_id"]
    user_id = setup_org_and_user["user_id"]

    payload = {
        "organization_id": org_id,
        "user_id": user_id,
        "title": "Onboarding Architecture Discussion",
    }
    res = client.post("/api/v1/assistant/conversations", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Onboarding Architecture Discussion"
    assert data["organization_id"] == org_id
    assert data["user_id"] == user_id
    assert data["message_count"] == 0
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.anyio
async def test_create_conversation_nonexistent_org(client: TestClient, setup_org_and_user):
    user_id = setup_org_and_user["user_id"]
    random_org_id = str(uuid.uuid4())

    res = client.post(
        "/api/v1/assistant/conversations",
        json={"organization_id": random_org_id, "user_id": user_id, "title": "Orphan Chat"},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_create_conversation_nonexistent_user(client: TestClient, setup_org_and_user):
    org_id = setup_org_and_user["org_id"]
    random_user_id = str(uuid.uuid4())

    res = client.post(
        "/api/v1/assistant/conversations",
        json={"organization_id": org_id, "user_id": random_user_id, "title": "Ghost User Chat"},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_create_conversation_blank_title_rejected(client: TestClient, setup_org_and_user):
    org_id = setup_org_and_user["org_id"]
    user_id = setup_org_and_user["user_id"]

    res = client.post(
        "/api/v1/assistant/conversations",
        json={"organization_id": org_id, "user_id": user_id, "title": "   "},
    )
    assert res.status_code in (400, 422)


@pytest.mark.anyio
async def test_list_conversations(client: TestClient, setup_org_and_user):
    org1_id = setup_org_and_user["org_id"]
    user1_id = setup_org_and_user["user_id"]

    # Second org and user
    org2 = client.post("/api/v1/organizations", json={"name": "Org 2", "slug": "org-2-chat"}).json()
    org2_id = org2["id"]
    user2 = client.post("/api/v1/users", json={"email": "user2@orvex.com", "full_name": "User Two"}).json()
    user2_id = user2["id"]

    client.post("/api/v1/assistant/conversations", json={"organization_id": org1_id, "user_id": user1_id, "title": "Org 1 Chat A"})
    client.post("/api/v1/assistant/conversations", json={"organization_id": org1_id, "user_id": user1_id, "title": "Org 1 Chat B"})
    client.post("/api/v1/assistant/conversations", json={"organization_id": org2_id, "user_id": user2_id, "title": "Org 2 Chat A"})

    # List all
    all_res = client.get("/api/v1/assistant/conversations")
    assert all_res.status_code == 200
    all_titles = [c["title"] for c in all_res.json()]
    assert "Org 1 Chat A" in all_titles
    assert "Org 1 Chat B" in all_titles
    assert "Org 2 Chat A" in all_titles

    # Filtered by org1
    org1_res = client.get(f"/api/v1/assistant/conversations?organization_id={org1_id}")
    assert org1_res.status_code == 200
    org1_titles = [c["title"] for c in org1_res.json()]
    assert "Org 1 Chat A" in org1_titles
    assert "Org 1 Chat B" in org1_titles
    assert "Org 2 Chat A" not in org1_titles


@pytest.mark.anyio
async def test_get_conversation_by_id(client: TestClient, setup_org_and_user):
    org_id = setup_org_and_user["org_id"]
    user_id = setup_org_and_user["user_id"]

    conv = client.post(
        "/api/v1/assistant/conversations",
        json={"organization_id": org_id, "user_id": user_id, "title": "Specific Chat"},
    ).json()
    conv_id = conv["id"]

    res = client.get(f"/api/v1/assistant/conversations/{conv_id}")
    assert res.status_code == 200
    assert res.json()["id"] == conv_id
    assert res.json()["title"] == "Specific Chat"


@pytest.mark.anyio
async def test_get_conversation_not_found(client: TestClient):
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/assistant/conversations/{random_id}")
    assert res.status_code == 404


@pytest.mark.anyio
async def test_update_conversation_title(client: TestClient, setup_org_and_user):
    org_id = setup_org_and_user["org_id"]
    user_id = setup_org_and_user["user_id"]

    conv = client.post(
        "/api/v1/assistant/conversations",
        json={"organization_id": org_id, "user_id": user_id, "title": "Old Title"},
    ).json()
    conv_id = conv["id"]

    patch_res = client.patch(
        f"/api/v1/assistant/conversations/{conv_id}",
        json={"title": "Updated Title"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Title"


@pytest.mark.anyio
async def test_delete_conversation(client: TestClient, setup_org_and_user):
    org_id = setup_org_and_user["org_id"]
    user_id = setup_org_and_user["user_id"]

    conv = client.post(
        "/api/v1/assistant/conversations",
        json={"organization_id": org_id, "user_id": user_id, "title": "To Delete"},
    ).json()
    conv_id = conv["id"]

    del_res = client.delete(f"/api/v1/assistant/conversations/{conv_id}")
    assert del_res.status_code == 204

    # Confirm 404
    get_res = client.get(f"/api/v1/assistant/conversations/{conv_id}")
    assert get_res.status_code == 404


@pytest.mark.anyio
async def test_cross_organization_conversation_isolation(client: TestClient, setup_org_and_user):
    org_a_id = setup_org_and_user["org_id"]
    user_a_id = setup_org_and_user["user_id"]

    conv_a = client.post(
        "/api/v1/assistant/conversations",
        json={"organization_id": org_a_id, "user_id": user_a_id, "title": "Conversation A"},
    ).json()
    conv_a_id = conv_a["id"]

    # Organization B
    org_b = client.post("/api/v1/organizations", json={"name": "Org B", "slug": "org-b-chat-iso"}).json()
    org_b_id = org_b["id"]

    # Scoped to Org B, accessing Conversation A must return 404
    cross_get = client.get(f"/api/v1/assistant/conversations/{conv_a_id}?organization_id={org_b_id}")
    assert cross_get.status_code == 404

    # Scoped to Org B, updating Conversation A must return 404
    cross_patch = client.patch(
        f"/api/v1/assistant/conversations/{conv_a_id}?organization_id={org_b_id}",
        json={"title": "Hijacked"},
    )
    assert cross_patch.status_code == 404

    # Scoped to Org B, deleting Conversation A must return 404
    cross_del = client.delete(f"/api/v1/assistant/conversations/{conv_a_id}?organization_id={org_b_id}")
    assert cross_del.status_code == 404

    # Conversation A still exists under Org A
    verify = client.get(f"/api/v1/assistant/conversations/{conv_a_id}?organization_id={org_a_id}")
    assert verify.status_code == 200
    assert verify.json()["title"] == "Conversation A"


# ==========================================
# Message Tests
# ==========================================

@pytest.fixture
def setup_conversation(client: TestClient, setup_org_and_user):
    org_id = setup_org_and_user["org_id"]
    user_id = setup_org_and_user["user_id"]

    conv = client.post(
        "/api/v1/assistant/conversations",
        json={"organization_id": org_id, "user_id": user_id, "title": "Chat for Messages"},
    ).json()
    return {"org_id": org_id, "user_id": user_id, "conv_id": conv["id"]}


@pytest.mark.anyio
async def test_create_user_message(client: TestClient, setup_conversation):
    conv_id = setup_conversation["conv_id"]

    payload = {
        "role": "user",
        "content": "What can ORVEX help me automate?",
    }
    res = client.post(f"/api/v1/assistant/conversations/{conv_id}/messages", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["role"] == "user"
    assert data["content"] == "What can ORVEX help me automate?"
    assert data["conversation_id"] == conv_id
    assert "id" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_create_assistant_message(client: TestClient, setup_conversation):
    conv_id = setup_conversation["conv_id"]

    payload = {
        "role": "assistant",
        "content": "ORVEX provides workflow automation and intelligent agent orchestration.",
        "tokens_used": 150,
        "latency_ms": 420,
    }
    res = client.post(f"/api/v1/assistant/conversations/{conv_id}/messages", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["role"] == "assistant"
    assert data["tokens_used"] == 150
    assert data["latency_ms"] == 420


@pytest.mark.anyio
async def test_list_conversation_messages(client: TestClient, setup_conversation):
    conv_id = setup_conversation["conv_id"]

    client.post(f"/api/v1/assistant/conversations/{conv_id}/messages", json={"role": "user", "content": "Question 1"})
    client.post(f"/api/v1/assistant/conversations/{conv_id}/messages", json={"role": "assistant", "content": "Answer 1"})

    res = client.get(f"/api/v1/assistant/conversations/{conv_id}/messages")
    assert res.status_code == 200
    messages = res.json()
    assert len(messages) == 2
    assert messages[0]["content"] == "Question 1"
    assert messages[0]["role"] == "user"
    assert messages[1]["content"] == "Answer 1"
    assert messages[1]["role"] == "assistant"


@pytest.mark.anyio
async def test_get_message_by_id(client: TestClient, setup_conversation):
    conv_id = setup_conversation["conv_id"]

    msg = client.post(
        f"/api/v1/assistant/conversations/{conv_id}/messages",
        json={"role": "user", "content": "Fetch me"},
    ).json()
    msg_id = msg["id"]

    res = client.get(f"/api/v1/assistant/messages/{msg_id}")
    assert res.status_code == 200
    assert res.json()["id"] == msg_id
    assert res.json()["content"] == "Fetch me"


@pytest.mark.anyio
async def test_create_message_nonexistent_conversation(client: TestClient):
    random_conv_id = str(uuid.uuid4())
    res = client.post(
        f"/api/v1/assistant/conversations/{random_conv_id}/messages",
        json={"role": "user", "content": "Lost message"},
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_get_nonexistent_message(client: TestClient):
    random_msg_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/assistant/messages/{random_msg_id}")
    assert res.status_code == 404


@pytest.mark.anyio
async def test_create_message_blank_content_rejected(client: TestClient, setup_conversation):
    conv_id = setup_conversation["conv_id"]

    res = client.post(
        f"/api/v1/assistant/conversations/{conv_id}/messages",
        json={"role": "user", "content": "   "},
    )
    assert res.status_code in (400, 422)


@pytest.mark.anyio
async def test_create_message_invalid_role_rejected(client: TestClient, setup_conversation):
    conv_id = setup_conversation["conv_id"]

    res = client.post(
        f"/api/v1/assistant/conversations/{conv_id}/messages",
        json={"role": "superadmin", "content": "Hello"},
    )
    assert res.status_code in (400, 422)


@pytest.mark.anyio
async def test_cross_organization_message_isolation(client: TestClient, setup_conversation):
    conv_id = setup_conversation["conv_id"]

    # Create message in Conversation under Org A
    msg = client.post(
        f"/api/v1/assistant/conversations/{conv_id}/messages",
        json={"role": "user", "content": "Secret query in Org A"},
    ).json()
    msg_id = msg["id"]

    # Create Org B
    org_b = client.post("/api/v1/organizations", json={"name": "Org B Isolated", "slug": "org-b-isolated-msg"}).json()
    org_b_id = org_b["id"]

    # Org B trying to list messages of Conversation A -> 404
    iso_list = client.get(f"/api/v1/assistant/conversations/{conv_id}/messages?organization_id={org_b_id}")
    assert iso_list.status_code == 404

    # Org B trying to get Message A -> 404
    iso_get = client.get(f"/api/v1/assistant/messages/{msg_id}?organization_id={org_b_id}")
    assert iso_get.status_code == 404

    # Org B trying to post message to Conversation A -> 404
    iso_post = client.post(
        f"/api/v1/assistant/conversations/{conv_id}/messages?organization_id={org_b_id}",
        json={"role": "user", "content": "Intruder message"},
    )
    assert iso_post.status_code == 404


@pytest.mark.anyio
async def test_cascade_delete_conversation_removes_messages(client: TestClient, setup_conversation):
    conv_id = setup_conversation["conv_id"]

    # Add message
    msg = client.post(
        f"/api/v1/assistant/conversations/{conv_id}/messages",
        json={"role": "user", "content": "I will be deleted"},
    ).json()
    msg_id = msg["id"]

    # Delete conversation
    del_res = client.delete(f"/api/v1/assistant/conversations/{conv_id}")
    assert del_res.status_code == 204

    # Message must be gone
    msg_get = client.get(f"/api/v1/assistant/messages/{msg_id}")
    assert msg_get.status_code == 404

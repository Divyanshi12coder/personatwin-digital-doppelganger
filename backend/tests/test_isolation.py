"""User-level data isolation: User B must never see or touch User A's memories."""

from fastapi.testclient import TestClient

from tests.conftest import CAREER_EXPERIENCE, LEARNING_NOTE, onboard, signup


def _setup(client: TestClient) -> tuple[dict[str, str], dict[str, str], dict[str, int]]:
    alice = signup(client, "alice@example.com", "Alice")
    bob = signup(client, "bob@example.com", "Bob")
    onboard(client, alice)
    doc = client.post("/api/knowledge", json=LEARNING_NOTE, headers=alice).json()
    exp = client.post("/api/experiences", json=CAREER_EXPERIENCE, headers=alice).json()
    chat = client.post("/api/chat", json={"message": "Should I switch careers?"}, headers=alice).json()
    msg_id = chat["assistant_message"]["id"]
    mem = client.post(f"/api/chat/messages/{msg_id}/remember", headers=alice).json()
    ids = {
        "doc": doc["id"],
        "exp": exp["id"],
        "conv": chat["conversation_id"],
        "msg": msg_id,
        "mem": mem["memory_id"],
    }
    return alice, bob, ids


def test_direct_access_is_denied(client: TestClient) -> None:
    alice, bob, ids = _setup(client)
    forbidden = [
        ("GET", f"/api/knowledge/{ids['doc']}"),
        ("PATCH", f"/api/knowledge/{ids['doc']}"),
        ("DELETE", f"/api/knowledge/{ids['doc']}"),
        ("GET", f"/api/experiences/{ids['exp']}"),
        ("PATCH", f"/api/experiences/{ids['exp']}"),
        ("DELETE", f"/api/experiences/{ids['exp']}"),
        ("GET", f"/api/conversations/{ids['conv']}"),
        ("PATCH", f"/api/conversations/{ids['conv']}"),
        ("DELETE", f"/api/conversations/{ids['conv']}"),
        ("POST", f"/api/chat/messages/{ids['msg']}/regenerate"),
        ("PATCH", f"/api/chat/messages/{ids['msg']}/feedback"),
        ("POST", f"/api/chat/messages/{ids['msg']}/remember"),
        ("GET", f"/api/memories/conversation/{ids['mem']}"),
        ("PATCH", f"/api/memories/conversation/{ids['mem']}"),
        ("DELETE", f"/api/memories/conversation/{ids['mem']}"),
    ]
    payloads = {"PATCH": {"title": "pwned", "feedback": "down"}}
    for method, path in forbidden:
        res = client.request(method, path, json=payloads.get(method), headers=bob)
        assert res.status_code == 404, f"{method} {path} -> {res.status_code}"
    # Alice's data is untouched.
    assert client.get(f"/api/knowledge/{ids['doc']}", headers=alice).json()["title"] == LEARNING_NOTE["title"]
    assert client.get(f"/api/conversations/{ids['conv']}", headers=alice).status_code == 200


def test_bob_cannot_continue_alices_conversation(client: TestClient) -> None:
    _, bob, ids = _setup(client)
    res = client.post("/api/chat", json={"message": "hi", "conversation_id": ids["conv"]}, headers=bob)
    assert res.status_code == 404


def test_listings_and_search_are_scoped(client: TestClient) -> None:
    alice, bob, _ = _setup(client)
    assert client.get("/api/knowledge", headers=bob).json()["total"] == 0
    assert client.get("/api/experiences", headers=bob).json() == []
    assert client.get("/api/conversations", headers=bob).json() == []
    assert client.get("/api/memories/conversation", headers=bob).json() == []
    assert client.get("/api/memories/tags", headers=bob).json() == []
    search = client.get("/api/memories", params={"q": "switch careers banking"}, headers=bob).json()
    assert [i for i in search["items"] if i["type"] != "preference"] == []
    overview = client.get("/api/insights/overview", headers=bob).json()
    assert overview["counts"]["total_memories"] == 0
    # ...while Alice sees her own.
    assert client.get("/api/knowledge", headers=alice).json()["total"] == 1


def test_chat_retrieval_never_uses_other_users_memories(client: TestClient) -> None:
    _, bob, _ = _setup(client)
    res = client.post("/api/chat", json={"message": "Should I switch careers from banking?"}, headers=bob)
    assert res.status_code == 200
    reply = res.json()["assistant_message"]
    assert reply["sources"] == []
    assert reply["grounding"] == "ungrounded"
    assert "bank job" not in reply["content"].lower()
    assert "don't have anything in my notes" in reply["content"]


def test_tags_are_per_user(client: TestClient) -> None:
    alice, bob, _ = _setup(client)
    client.post("/api/knowledge", json={**LEARNING_NOTE, "tags": ["study"]}, headers=bob)
    alice_tags = {t["name"]: t["count"] for t in client.get("/api/memories/tags", headers=alice).json()}
    bob_tags = {t["name"]: t["count"] for t in client.get("/api/memories/tags", headers=bob).json()}
    assert bob_tags == {"study": 1}
    assert alice_tags["study"] == 1

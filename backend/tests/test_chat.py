"""End-to-end chat orchestration (demo provider) + AI service behaviour."""

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.services.ai import AIProviderError, AIService, DemoProvider, GenerationRequest, build_ai_service
from tests.conftest import CAREER_EXPERIENCE, LEARNING_NOTE, onboard


def _seed(client: TestClient, auth: dict[str, str]) -> None:
    onboard(client, auth)
    client.post("/api/knowledge", json=LEARNING_NOTE, headers=auth)
    client.post("/api/experiences", json=CAREER_EXPERIENCE, headers=auth)


def test_chat_is_grounded_in_retrieved_experience(client: TestClient, auth: dict[str, str]) -> None:
    _seed(client, auth)
    res = client.post("/api/chat", json={"message": "I'm struggling to decide whether I should switch careers."}, headers=auth)
    assert res.status_code == 200, res.text
    body = res.json()
    reply = body["assistant_message"]
    assert body["persisted"] is True
    assert body["conversation_id"] is not None
    assert reply["grounding"] == "grounded"
    assert reply["provider"] == "demo"
    labels = {s["label"]: s for s in reply["sources"]}
    assert "E1" in labels and labels["E1"]["cited"] is True
    assert labels["E1"]["title"] == CAREER_EXPERIENCE["title"]
    assert "[E1]" in reply["content"]
    assert "financial runway" in reply["content"]
    steps = [s["step"] for s in reply["trace"]["steps"]]
    assert steps == ["understand", "retrieve", "persona", "assemble", "prompt", "generate", "validate"]
    assert reply["trace"]["topic"] in ("career", "decision_making")


def test_chat_without_memories_admits_it(client: TestClient, auth: dict[str, str]) -> None:
    onboard(client, auth)
    res = client.post("/api/chat", json={"message": "How do I negotiate a salary?"}, headers=auth).json()
    reply = res["assistant_message"]
    assert reply["grounding"] == "ungrounded"
    assert reply["sources"] == []
    assert "don't have anything in my notes" in reply["content"]


def test_personal_question_without_experience_is_not_invented(client: TestClient, auth: dict[str, str]) -> None:
    onboard(client, auth)
    client.post("/api/knowledge", json=LEARNING_NOTE, headers=auth)
    res = client.post("/api/chat", json={"message": "Have you ever been fired from a job?"}, headers=auth).json()
    content = res["assistant_message"]["content"]
    assert "don't have a recorded experience" in content


def test_conversation_history_and_short_term_memory(client: TestClient, auth: dict[str, str]) -> None:
    _seed(client, auth)
    first = client.post("/api/chat", json={"message": "Should I switch careers?"}, headers=auth).json()
    conv_id = first["conversation_id"]
    second = client.post(
        "/api/chat", json={"message": "What would be a good first experiment?", "conversation_id": conv_id}, headers=auth
    ).json()
    assert second["conversation_id"] == conv_id
    prompt_step = next(s for s in second["assistant_message"]["trace"]["steps"] if s["step"] == "prompt")
    assert prompt_step["detail"].startswith("2 prior turns")

    detail = client.get(f"/api/conversations/{conv_id}", headers=auth).json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant", "user", "assistant"]
    listing = client.get("/api/conversations", headers=auth).json()
    assert listing[0]["message_count"] == 4

    renamed = client.patch(f"/api/conversations/{conv_id}", json={"title": "Career switch"}, headers=auth)
    assert renamed.json()["title"] == "Career switch"
    assert client.delete(f"/api/conversations/{conv_id}", headers=auth).status_code == 204
    assert client.get("/api/conversations", headers=auth).json() == []


def test_regenerate_feedback_and_remember(client: TestClient, auth: dict[str, str]) -> None:
    _seed(client, auth)
    res = client.post("/api/chat", json={"message": "How should I study for a hard exam?"}, headers=auth).json()
    msg_id = res["assistant_message"]["id"]

    regen = client.post(f"/api/chat/messages/{msg_id}/regenerate", headers=auth)
    assert regen.status_code == 200
    assert regen.json()["id"] == msg_id
    assert any(s["source_type"] == "knowledge" for s in regen.json()["sources"])

    fb = client.patch(f"/api/chat/messages/{msg_id}/feedback", json={"feedback": "up"}, headers=auth)
    assert fb.json()["feedback"] == "up"
    assert client.patch(f"/api/chat/messages/{msg_id}/feedback", json={"feedback": "meh"}, headers=auth).status_code == 422

    user_msg_id = res["user_message"]["id"]
    assert client.post(f"/api/chat/messages/{user_msg_id}/regenerate", headers=auth).status_code == 400

    remembered = client.post(f"/api/chat/messages/{msg_id}/remember", headers=auth)
    assert remembered.status_code == 201
    mems = client.get("/api/memories/conversation", headers=auth).json()
    assert len(mems) == 1
    assert mems[0]["content"].startswith("Question: How should I study")
    assert mems[0]["indexed"] is True


def test_conversation_memory_is_retrieved_and_labelled(client: TestClient, auth: dict[str, str]) -> None:
    onboard(client, auth)
    first = client.post("/api/chat", json={"message": "How do I stop procrastinating on my thesis?"}, headers=auth).json()
    client.post(f"/api/chat/messages/{first['assistant_message']['id']}/remember", headers=auth)
    later = client.post("/api/chat", json={"message": "I keep procrastinating on my thesis again"}, headers=auth).json()
    sources = later["assistant_message"]["sources"]
    assert any(s["source_type"] == "conversation" and s["label"].startswith("C") for s in sources)


def test_privacy_mode_persists_nothing(client: TestClient, auth: dict[str, str]) -> None:
    _seed(client, auth)
    settings = client.get("/api/settings", headers=auth).json()
    client.put("/api/settings", json={**settings, "save_conversations": False}, headers=auth)
    res = client.post(
        "/api/chat",
        json={
            "message": "And what about the money side?",
            "history": [
                {"role": "user", "content": "Should I switch careers?"},
                {"role": "assistant", "content": "Let's think it through."},
            ],
        },
        headers=auth,
    ).json()
    assert res["persisted"] is False
    assert res["conversation_id"] is None
    assert res["assistant_message"]["id"] is None
    assert client.get("/api/conversations", headers=auth).json() == []


def test_auto_remember_setting(client: TestClient, auth: dict[str, str]) -> None:
    onboard(client, auth)
    settings = client.get("/api/settings", headers=auth).json()
    client.put("/api/settings", json={**settings, "auto_remember": True}, headers=auth)
    res = client.post("/api/chat", json={"message": "How do I set better goals this year?"}, headers=auth).json()
    assert res["remembered_memory_id"] is not None


def test_chat_validation(client: TestClient, auth: dict[str, str]) -> None:
    assert client.post("/api/chat", json={"message": "   "}, headers=auth).status_code == 422
    assert client.post("/api/chat", json={"message": "x" * 5000}, headers=auth).status_code == 422
    assert client.post("/api/chat", json={"message": "hi", "conversation_id": 999}, headers=auth).status_code == 404


# ------------------------------------------------------------------ AI service


class _FailingProvider:
    name = "anthropic"
    model = "claude-opus-5"

    def generate(self, request: GenerationRequest):  # type: ignore[no-untyped-def]
        raise AIProviderError("Could not reach the AI provider.")


def test_ai_service_degrades_to_demo_with_notice(client: TestClient, auth: dict[str, str], monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from app.services import chat as chat_module

    _seed(client, auth)
    monkeypatch.setattr(chat_module, "get_ai_service", lambda: AIService(_FailingProvider(), fallback=DemoProvider()))
    res = client.post("/api/chat", json={"message": "Should I switch careers?"}, headers=auth).json()
    trace = res["assistant_message"]["trace"]
    assert trace["degraded"] is True
    assert "Could not reach the AI provider" in trace["notice"]
    assert res["assistant_message"]["provider"] == "demo"


def test_ai_service_without_fallback_returns_503(client: TestClient, auth: dict[str, str], monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from app.services import chat as chat_module

    onboard(client, auth)
    monkeypatch.setattr(chat_module, "get_ai_service", lambda: AIService(_FailingProvider()))
    res = client.post("/api/chat", json={"message": "Should I switch careers?"}, headers=auth)
    assert res.status_code == 503
    assert "Could not reach" in res.json()["detail"]


def test_build_ai_service_selects_provider() -> None:
    assert build_ai_service(Settings(AI_PROVIDER="demo")).provider.name == "demo"
    # A provider without a key falls back to demo mode instead of crashing.
    assert build_ai_service(Settings(AI_PROVIDER="anthropic", AI_API_KEY="")).provider.name == "demo"
    live = build_ai_service(Settings(AI_PROVIDER="anthropic", AI_API_KEY="sk-ant-test"))
    assert live.provider.name == "anthropic"
    assert live.provider.model == "claude-opus-5"
    assert live.fallback is not None
    openai = build_ai_service(Settings(AI_PROVIDER="openai", AI_API_KEY="sk-test", AI_MODEL="gpt-4o-mini"))
    assert openai.provider.name == "openai"

"""Knowledge, experience, profile and memory-inspector CRUD through the API."""

from fastapi.testclient import TestClient

from tests.conftest import CAREER_EXPERIENCE, LEARNING_NOTE, ONBOARDING, onboard


def test_onboarding_and_profile(client: TestClient, auth: dict[str, str]) -> None:
    before = client.get("/api/profile", headers=auth).json()
    assert before["mentor"] is None
    assert before["completeness"] < 50

    onboard(client, auth)
    profile = client.get("/api/profile", headers=auth).json()
    assert profile["mentor"]["mentor_name"] == "Ada's Twin"
    assert profile["mentor"]["onboarding_completed"] is True
    assert profile["personality"]["teaching_approach"] == "step_by_step"
    assert profile["completeness"] == 100
    assert client.get("/api/auth/me", headers=auth).json()["onboarding_completed"] is True


def test_personality_validation(client: TestClient, auth: dict[str, str]) -> None:
    bad = {**ONBOARDING["personality"], "tone": "sarcastic"}
    res = client.put("/api/profile/personality", json=bad, headers=auth)
    assert res.status_code == 422
    slider = {**ONBOARDING["personality"], "warmth": 150}
    assert client.put("/api/profile/personality", json=slider, headers=auth).status_code == 422
    good = {**ONBOARDING["personality"], "tone": "candid", "humor": 70}
    res = client.put("/api/profile/personality", json=good, headers=auth)
    assert res.status_code == 200
    assert res.json()["personality"]["tone"] == "candid"


def test_options_endpoint(client: TestClient) -> None:
    opts = client.get("/api/profile/options").json()
    assert "communication_style" in opts["persona"]
    assert any(o["value"] == "failure" for o in opts["experience_types"])


def test_knowledge_crud_and_chunking(client: TestClient, auth: dict[str, str]) -> None:
    res = client.post("/api/knowledge", json=LEARNING_NOTE, headers=auth)
    assert res.status_code == 201, res.text
    doc = res.json()
    assert doc["chunk_count"] >= 1
    assert doc["indexed"] is True
    assert doc["tags"] == ["study", "memory"]

    long_doc = {"title": "Long", "content": "\n\n".join(f"Paragraph {i}. " + "word " * 60 for i in range(12))}
    long_res = client.post("/api/knowledge", json=long_doc, headers=auth).json()
    assert long_res["chunk_count"] > 3

    listing = client.get("/api/knowledge", headers=auth).json()
    assert listing["total"] == 2
    assert client.get("/api/knowledge?category=learning", headers=auth).json()["total"] == 1
    assert client.get("/api/knowledge?tag=study", headers=auth).json()["total"] == 1
    assert client.get("/api/knowledge?q=spaced", headers=auth).json()["total"] == 1

    updated = client.patch(
        f"/api/knowledge/{doc['id']}", json={"title": "Learning playbook", "tags": ["Study", "focus"]}, headers=auth
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Learning playbook"
    assert updated.json()["tags"] == ["study", "focus"]

    assert client.delete(f"/api/knowledge/{doc['id']}", headers=auth).status_code == 204
    assert client.get(f"/api/knowledge/{doc['id']}", headers=auth).status_code == 404


def test_knowledge_validation(client: TestClient, auth: dict[str, str]) -> None:
    assert client.post("/api/knowledge", json={"title": "", "content": "x"}, headers=auth).status_code == 422
    assert client.post("/api/knowledge", json={"title": "x", "content": "   "}, headers=auth).status_code == 422
    assert (
        client.post("/api/knowledge", json={"title": "x", "content": "y", "category": "nope"}, headers=auth).status_code
        == 422
    )


def test_knowledge_upload(client: TestClient, auth: dict[str, str]) -> None:
    files = {"file": ("notes.md", b"# Notes\n\nDeliberate practice means working at the edge of your ability.", "text/markdown")}
    res = client.post("/api/knowledge/upload", files=files, data={"category": "learning", "tags": "practice, skills"}, headers=auth)
    assert res.status_code == 201, res.text
    assert res.json()["source_type"] == "document"
    assert res.json()["title"] == "notes"
    assert res.json()["tags"] == ["practice", "skills"]

    bad = {"file": ("evil.exe", b"MZ....", "application/octet-stream")}
    assert client.post("/api/knowledge/upload", files=bad, headers=auth).status_code == 422
    fake_pdf = {"file": ("x.pdf", b"not a pdf", "application/pdf")}
    assert client.post("/api/knowledge/upload", files=fake_pdf, headers=auth).status_code == 422


def test_url_import_blocks_private_addresses(client: TestClient, auth: dict[str, str]) -> None:
    for url in ("http://127.0.0.1:8000/api/health", "http://localhost/", "http://169.254.169.254/latest/meta-data"):
        res = client.post("/api/knowledge/url", json={"url": url}, headers=auth)
        assert res.status_code == 422, url
    assert client.post("/api/knowledge/url", json={"url": "ftp://example.com/x"}, headers=auth).status_code == 422


def test_experience_crud(client: TestClient, auth: dict[str, str]) -> None:
    res = client.post("/api/experiences", json=CAREER_EXPERIENCE, headers=auth)
    assert res.status_code == 201, res.text
    exp = res.json()
    assert exp["indexed"] is True
    assert exp["tags"] == ["career change", "risk"]

    assert client.get("/api/experiences?experience_type=career", headers=auth).json()[0]["id"] == exp["id"]
    assert client.get("/api/experiences?q=banking", headers=auth).json()[0]["id"] == exp["id"]
    assert client.get("/api/experiences?tag=risk", headers=auth).json()[0]["id"] == exp["id"]

    upd = client.patch(f"/api/experiences/{exp['id']}", json={"importance": 4, "context": "2016"}, headers=auth)
    assert upd.status_code == 200
    assert upd.json()["importance"] == 4

    assert client.delete(f"/api/experiences/{exp['id']}", headers=auth).status_code == 204
    assert client.get("/api/experiences", headers=auth).json() == []


def test_experience_validation(client: TestClient, auth: dict[str, str]) -> None:
    empty = {"title": "Something", "experience_type": "lesson"}
    assert client.post("/api/experiences", json=empty, headers=auth).status_code == 422
    future = {**CAREER_EXPERIENCE, "occurred_on": "2999-01-01"}
    assert client.post("/api/experiences", json=future, headers=auth).status_code == 422
    bad_type = {**CAREER_EXPERIENCE, "experience_type": "dream"}
    assert client.post("/api/experiences", json=bad_type, headers=auth).status_code == 422
    importance = {**CAREER_EXPERIENCE, "importance": 9}
    assert client.post("/api/experiences", json=importance, headers=auth).status_code == 422


def test_memory_inspector_lists_and_searches(client: TestClient, auth: dict[str, str]) -> None:
    onboard(client, auth)
    client.post("/api/knowledge", json=LEARNING_NOTE, headers=auth)
    client.post("/api/experiences", json=CAREER_EXPERIENCE, headers=auth)

    everything = client.get("/api/memories", headers=auth).json()
    types = {i["type"] for i in everything["items"]}
    assert {"knowledge", "experience", "preference"} <= types
    assert everything["counts"]["knowledge"] == 1
    assert everything["counts"]["experience"] == 1

    search = client.get("/api/memories", params={"q": "should I switch careers"}, headers=auth).json()
    assert search["items"][0]["type"] == "experience"
    assert search["items"][0]["relevance"] is not None

    only_knowledge = client.get("/api/memories", params={"type": "knowledge"}, headers=auth).json()
    assert {i["type"] for i in only_knowledge["items"]} == {"knowledge"}

    tags = client.get("/api/memories/tags", headers=auth).json()
    assert {"name": "career change", "count": 1} in tags

    reindex = client.post("/api/memories/reindex", headers=auth).json()
    assert reindex == {"knowledge_documents": 1, "experiences": 1, "conversation_memories": 0}


def test_settings_roundtrip_and_validation(client: TestClient, auth: dict[str, str]) -> None:
    defaults = client.get("/api/settings", headers=auth).json()
    assert defaults["save_conversations"] is True
    new = {**defaults, "retrieval_top_k": 4, "auto_remember": True, "creativity": 0.2}
    res = client.put("/api/settings", json=new, headers=auth)
    assert res.status_code == 200
    assert res.json()["retrieval_top_k"] == 4
    assert client.put("/api/settings", json={**new, "retrieval_top_k": 99}, headers=auth).status_code == 422


def test_data_export(client: TestClient, auth: dict[str, str]) -> None:
    onboard(client, auth)
    client.post("/api/knowledge", json=LEARNING_NOTE, headers=auth)
    data = client.get("/api/auth/export", headers=auth).json()
    assert data["mentor_profile"]["mentor_name"] == "Ada's Twin"
    assert data["knowledge"][0]["title"] == LEARNING_NOTE["title"]
    assert "embedding" not in str(data)

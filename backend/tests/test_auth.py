from fastapi.testclient import TestClient

from tests.conftest import signup


def test_health(client: TestClient) -> None:
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["ai"]["mode"] == "demo"


def test_signup_login_me(client: TestClient) -> None:
    headers = signup(client, "grace@example.com", "Grace Hopper")
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "grace@example.com"
    assert me.json()["onboarding_completed"] is False

    login = client.post("/api/auth/login", json={"email": "GRACE@example.com", "password": "analytical1"})
    assert login.status_code == 200
    assert login.json()["user"]["full_name"] == "Grace Hopper"


def test_password_is_hashed_not_stored(client: TestClient, db_session) -> None:  # type: ignore[no-untyped-def]
    from app.models import User

    signup(client, "hash@example.com")
    user = db_session.query(User).filter_by(email="hash@example.com").one()
    assert user.password_hash != "analytical1"
    assert user.password_hash.startswith("$2")


def test_duplicate_email_rejected(client: TestClient) -> None:
    signup(client, "dup@example.com")
    res = client.post("/api/auth/signup", json={"email": "dup@example.com", "full_name": "X", "password": "analytical1"})
    assert res.status_code == 409


def test_signup_validation(client: TestClient) -> None:
    weak = client.post("/api/auth/signup", json={"email": "a@example.com", "full_name": "A", "password": "short"})
    assert weak.status_code == 422
    no_digit = client.post(
        "/api/auth/signup", json={"email": "a@example.com", "full_name": "A", "password": "onlyletters"}
    )
    assert no_digit.status_code == 422
    assert "number" in no_digit.json()["detail"]
    bad_email = client.post("/api/auth/signup", json={"email": "nope", "full_name": "A", "password": "analytical1"})
    assert bad_email.status_code == 422


def test_wrong_password(client: TestClient) -> None:
    signup(client, "w@example.com")
    res = client.post("/api/auth/login", json={"email": "w@example.com", "password": "wrongpass1"})
    assert res.status_code == 401
    unknown = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "wrongpass1"})
    assert unknown.status_code == 401
    assert unknown.json()["detail"] == res.json()["detail"]  # no account enumeration


def test_protected_routes_require_token(client: TestClient) -> None:
    for path in ("/api/auth/me", "/api/knowledge", "/api/experiences", "/api/memories", "/api/insights/overview"):
        assert client.get(path).status_code == 401
    bad = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert bad.status_code == 401


def test_logout_revokes_token(client: TestClient) -> None:
    headers = signup(client, "out@example.com")
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_change_password_rotates_tokens(client: TestClient) -> None:
    headers = signup(client, "pw@example.com")
    bad = client.post(
        "/api/auth/change-password",
        json={"current_password": "nope12345", "new_password": "newpass123"},
        headers=headers,
    )
    assert bad.status_code == 400
    res = client.post(
        "/api/auth/change-password",
        json={"current_password": "analytical1", "new_password": "newpass123"},
        headers=headers,
    )
    assert res.status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    new_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    assert client.get("/api/auth/me", headers=new_headers).status_code == 200
    assert client.post("/api/auth/login", json={"email": "pw@example.com", "password": "newpass123"}).status_code == 200


def test_delete_account_removes_data(client: TestClient) -> None:
    headers = signup(client, "bye@example.com")
    client.post("/api/knowledge", json={"title": "t", "content": "some content"}, headers=headers)
    wrong = client.request("DELETE", "/api/auth/me", json={"password": "wrong1234"}, headers=headers)
    assert wrong.status_code == 400
    res = client.request("DELETE", "/api/auth/me", json={"password": "analytical1"}, headers=headers)
    assert res.status_code == 204
    assert client.post("/api/auth/login", json={"email": "bye@example.com", "password": "analytical1"}).status_code == 401


def test_auth_rate_limit(client: TestClient) -> None:
    codes = [
        client.post("/api/auth/login", json={"email": "rl@example.com", "password": "x"}).status_code for _ in range(25)
    ]
    assert 429 in codes

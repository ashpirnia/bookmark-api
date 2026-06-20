def test_register_returns_201_with_user_and_token(client, user_payload):
    resp = client.post("/api/auth/register", json=user_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["username"] == user_payload["username"]
    assert data["user"]["email"] == user_payload["email"]
    assert "password_hash" not in data["user"]
    assert isinstance(data["token"], str) and len(data["token"]) > 0


def test_register_duplicate_email_returns_409(client, user_payload):
    client.post("/api/auth/register", json=user_payload)
    resp = client.post("/api/auth/register", json={**user_payload, "username": "other"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


def test_register_duplicate_username_returns_409(client, user_payload):
    client.post("/api/auth/register", json=user_payload)
    resp = client.post("/api/auth/register", json={**user_payload, "email": "other@example.com"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


def test_register_invalid_email_returns_422_error_envelope(client):
    resp = client.post("/api/auth/register", json={
        "username": "bob", "email": "invalid-email", "password": "password123",
    })
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"]["field"] == "email"


def test_register_password_too_short_returns_422_with_min_length(client):
    resp = client.post("/api/auth/register", json={
        "username": "bob", "email": "bob@example.com", "password": "short",
    })
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"]["field"] == "password"
    assert error["details"].get("min_length") == 8


def test_login_returns_200_with_token(client, user_payload, auth_token):
    resp = client.post("/api/auth/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == user_payload["email"]


def test_login_wrong_password_returns_401(client, user_payload, auth_token):
    resp = client.post("/api/auth/login", json={
        "email": user_payload["email"],
        "password": "wrongpassword",
    })
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


def test_login_unknown_email_returns_401(client):
    resp = client.post("/api/auth/login", json={
        "email": "unknown@example.com", "password": "password123",
    })
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"

import pytest
from openapi_core import OpenAPI
from openapi_core.testing import MockRequest, MockResponse

from app.main import app


@pytest.fixture(scope="module")
def openapi():
    return OpenAPI.from_dict(app.openapi())


def _validate_success_response(openapi: OpenAPI, resp, method: str, path: str, path_pattern: str):
    request = MockRequest(
        host_url="http://localhost",
        method=method,
        path=path,
        path_pattern=path_pattern,
    )
    response = MockResponse(
        data=resp.content,
        status_code=resp.status_code,
    )
    openapi.validate_response(request, response)


def _validate_error_response(resp):
    data = resp.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert isinstance(data["error"]["code"], str)
    assert isinstance(data["error"]["message"], str)


def test_register_response_matches_openapi_schema(client, openapi, user_payload):
    resp = client.post("/api/auth/register", json=user_payload)
    assert resp.status_code == 201
    _validate_success_response(openapi, resp, "post", "/api/auth/register", "/api/auth/register")


def test_login_response_matches_openapi_schema(client, openapi, user_payload, auth_token):
    resp = client.post("/api/auth/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"],
    })
    assert resp.status_code == 200
    _validate_success_response(openapi, resp, "post", "/api/auth/login", "/api/auth/login")


def test_create_bookmark_response_matches_openapi_schema(client, openapi, auth_headers):
    resp = client.post("/api/bookmarks", json={
        "url": "https://example.com", "title": "Test", "tags": ["python"],
    }, headers=auth_headers)
    assert resp.status_code == 201
    _validate_success_response(openapi, resp, "post", "/api/bookmarks", "/api/bookmarks")


def test_list_bookmarks_response_matches_openapi_schema(client, openapi, auth_headers):
    resp = client.get("/api/bookmarks", headers=auth_headers)
    assert resp.status_code == 200
    _validate_success_response(openapi, resp, "get", "/api/bookmarks", "/api/bookmarks")


def test_get_stats_response_matches_openapi_schema(client, openapi, auth_headers):
    resp = client.get("/api/bookmarks/stats", headers=auth_headers)
    assert resp.status_code == 200
    _validate_success_response(openapi, resp, "get", "/api/bookmarks/stats", "/api/bookmarks/stats")


def test_all_error_responses_follow_consistent_envelope(client, auth_headers):
    """Every error, regardless of cause, must follow {"error": {"code": ..., "message": ...}}."""
    _validate_error_response(client.get("/api/bookmarks/99999", headers=auth_headers))
    _validate_error_response(client.post("/api/bookmarks", json={"url": "https://x.com"}, headers=auth_headers))
    _validate_error_response(client.post("/api/bookmarks", json={"url": "bad-url", "title": "T"}, headers=auth_headers))

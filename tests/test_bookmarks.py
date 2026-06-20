BOOKMARK_PAYLOAD = {
    "url": "https://example.com",
    "title": "Example Site",
    "description": "An example website",
    "tags": ["python", "web"],
}


def test_create_bookmark_returns_201(client, auth_headers):
    resp = client.post("/api/bookmarks", json=BOOKMARK_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == BOOKMARK_PAYLOAD["title"]
    assert {t["name"] for t in data["tags"]} == {"python", "web"}
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_bookmark_requires_auth(client):
    resp = client.post("/api/bookmarks", json=BOOKMARK_PAYLOAD)
    assert resp.status_code == 401


def test_create_bookmark_invalid_url_returns_422(client, auth_headers):
    resp = client.post("/api/bookmarks", json={**BOOKMARK_PAYLOAD, "url": "not-a-url"}, headers=auth_headers)
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"]["field"] == "url"


def test_create_bookmark_missing_title_returns_422(client, auth_headers):
    resp = client.post("/api/bookmarks", json={"url": "https://example.com"}, headers=auth_headers)
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"]["field"] == "title"


def test_create_bookmark_tags_normalised_to_lowercase(client, auth_headers):
    resp = client.post("/api/bookmarks", json={
        **BOOKMARK_PAYLOAD, "tags": ["Python", "WEB", " FastAPI "],
    }, headers=auth_headers)
    assert resp.status_code == 201
    assert {t["name"] for t in resp.json()["tags"]} == {"python", "web", "fastapi"}


def test_get_bookmark_returns_200(client, auth_headers, bookmark):
    resp = client.get(f"/api/bookmarks/{bookmark['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == bookmark["id"]


def test_get_bookmark_not_found_returns_404(client, auth_headers):
    resp = client.get("/api/bookmarks/99999", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_get_other_users_bookmark_returns_404(client, auth_headers, alt_auth_headers, bookmark):
    # Must not reveal that the bookmark exists — return 404, not 403
    resp = client.get(f"/api/bookmarks/{bookmark['id']}", headers=alt_auth_headers)
    assert resp.status_code == 404


def test_update_bookmark_partial_update(client, auth_headers, bookmark):
    resp = client.patch(
        f"/api/bookmarks/{bookmark['id']}",
        json={"title": "Updated Title"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated Title"
    assert data["url"] == bookmark["url"]  # unchanged


def test_delete_bookmark_returns_204_and_removes_resource(client, auth_headers, bookmark):
    resp = client.delete(f"/api/bookmarks/{bookmark['id']}", headers=auth_headers)
    assert resp.status_code == 204
    get_resp = client.get(f"/api/bookmarks/{bookmark['id']}", headers=auth_headers)
    assert get_resp.status_code == 404

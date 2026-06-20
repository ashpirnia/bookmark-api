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


def test_create_bookmark_reuses_existing_tag_row(client, auth_headers):
    client.post("/api/bookmarks", json={**BOOKMARK_PAYLOAD, "tags": ["python"]}, headers=auth_headers)
    resp = client.post("/api/bookmarks", json={**BOOKMARK_PAYLOAD, "tags": ["python"]}, headers=auth_headers)
    assert resp.status_code == 201
    # Both bookmarks reference the same tag id — no duplicate tag rows created
    list_resp = client.get("/api/bookmarks", headers=auth_headers)
    all_bookmarks = list_resp.json()["items"]
    python_ids = {t["id"] for bm in all_bookmarks for t in bm["tags"] if t["name"] == "python"}
    assert len(python_ids) == 1


def test_list_bookmarks_returns_paginated_response(client, auth_headers, bookmark):
    resp = client.get("/api/bookmarks", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) >= {"items", "total", "page", "page_size"}
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_bookmarks_filter_by_tag(client, auth_headers):
    client.post("/api/bookmarks", json={**BOOKMARK_PAYLOAD, "tags": ["python"]}, headers=auth_headers)
    client.post("/api/bookmarks", json={**BOOKMARK_PAYLOAD, "tags": ["javascript"]}, headers=auth_headers)
    resp = client.get("/api/bookmarks?tag=python", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 1
    assert all("python" in {t["name"] for t in bm["tags"]} for bm in data["items"])


def test_list_bookmarks_search_by_keyword(client, auth_headers):
    client.post("/api/bookmarks", json={"url": "https://a.com", "title": "FastAPI Tutorial", "tags": []}, headers=auth_headers)
    client.post("/api/bookmarks", json={"url": "https://b.com", "title": "Django Guide", "tags": []}, headers=auth_headers)
    resp = client.get("/api/bookmarks?q=fastapi", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "FastAPI Tutorial"


def test_list_bookmarks_pagination(client, auth_headers):
    for i in range(5):
        client.post("/api/bookmarks", json={
            "url": f"https://example{i}.com", "title": f"Site {i}", "tags": [],
        }, headers=auth_headers)
    resp = client.get("/api/bookmarks?page=1&page_size=2", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2


def test_list_bookmarks_user_isolation(client, auth_headers, alt_auth_headers):
    client.post("/api/bookmarks", json=BOOKMARK_PAYLOAD, headers=auth_headers)
    resp = client.get("/api/bookmarks", headers=alt_auth_headers)
    assert resp.json()["total"] == 0


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


def test_update_bookmark_clears_tags_when_empty_list_sent(client, auth_headers, bookmark):
    resp = client.patch(
        f"/api/bookmarks/{bookmark['id']}",
        json={"tags": []},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["tags"] == []


def test_delete_bookmark_returns_204_and_removes_resource(client, auth_headers, bookmark):
    resp = client.delete(f"/api/bookmarks/{bookmark['id']}", headers=auth_headers)
    assert resp.status_code == 204
    get_resp = client.get(f"/api/bookmarks/{bookmark['id']}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_get_stats_returns_correct_aggregations(client, auth_headers):
    client.post("/api/bookmarks", json={**BOOKMARK_PAYLOAD, "tags": ["python", "web"]}, headers=auth_headers)
    resp = client.get("/api/bookmarks/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_bookmarks"] == 1
    assert data["total_tags"] == 2
    assert len(data["top_tags"]) == 2
    assert all("name" in t and "count" in t for t in data["top_tags"])
    assert len(data["bookmarks_per_month"]) == 1

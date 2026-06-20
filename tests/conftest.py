import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def engine():
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    try:
        yield _engine
    finally:
        Base.metadata.drop_all(_engine)
        _engine.dispose()


@pytest.fixture
def client(engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def user_payload():
    return {"username": "testuser", "email": "test@example.com", "password": "testpassword"}


@pytest.fixture
def auth_token(client, user_payload):
    resp = client.post("/api/auth/register", json=user_payload)
    return resp.json()["token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def alt_auth_headers(client):
    """A second user — used for data-isolation tests."""
    resp = client.post("/api/auth/register", json={
        "username": "otheruser",
        "email": "other@example.com",
        "password": "otherpassword",
    })
    return {"Authorization": f"Bearer {resp.json()['token']}"}


@pytest.fixture
def bookmark(client, auth_headers):
    resp = client.post("/api/bookmarks", json={
        "url": "https://example.com",
        "title": "Example Site",
        "description": "An example",
        "tags": ["test"],
    }, headers=auth_headers)
    return resp.json()

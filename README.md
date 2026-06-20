# Bookmarks API

A personal bookmarks manager. Save, tag, search, and manage web bookmarks via a RESTful JSON API.

## Setup

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                # install dependencies
alembic upgrade head   # run database migrations (no env vars needed — defaults to SQLite)
```

## Running the server

```bash
SECRET_KEY=your-secret-key uv run uvicorn app.main:app --reload
```

`SECRET_KEY` is used to sign JWT tokens. In production, set it to a long random string (e.g. `openssl rand -hex 32`). Never use a placeholder value in production.

The server starts at `http://localhost:8000`. Interactive API docs are at `http://localhost:8000/docs`.

## Quick start

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "password123"}'

# Login — returns a token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "password123"}'
```

All subsequent requests require `Authorization: Bearer <token>`. The full endpoint reference is available at `/docs`.

## Running tests

```bash
uv run pytest
```

## Tech choices

- **FastAPI** — request validation, dependency injection, and auto-generated OpenAPI docs out of the box
- **SQLite + SQLAlchemy** — zero-setup relational database with a Python ORM; swap the `DATABASE_URL` in `app/database.py` to migrate to PostgreSQL
- **Alembic** — schema migrations
- **JWT (python-jose + bcrypt)** — stateless auth; tokens are signed with `SECRET_KEY` and expire after 24 hours

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Bookmark, Tag, User
from app.schemas import (
    BookmarkCreateRequest,
    BookmarkPerMonth,
    BookmarkResponse,
    BookmarkUpdateRequest,
    ErrorResponse,
    PaginatedBookmarkResponse,
    StatsResponse,
    TagCount,
)

_error = {"model": ErrorResponse}

router = APIRouter(
    prefix="/api/bookmarks",
    tags=["bookmarks"],
    responses={
        401: {**_error, "description": "Not authenticated"},
        422: {**_error, "description": "Validation error"},
    },
)


def _resolve_tags(names: list[str], db: Session) -> list[Tag]:
    tags = []
    for name in names:
        name = name.lower().strip()
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
        tags.append(tag)
    return tags


def _get_bookmark_or_404(bookmark_id: int, user: User, db: Session) -> Bookmark:
    bookmark = (
        db.query(Bookmark)
        .options(selectinload(Bookmark.tags))
        .filter(Bookmark.id == bookmark_id, Bookmark.user_id == user.id)
        .first()
    )
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    return bookmark


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    uid = current_user.id

    total_bookmarks = db.execute(
        text("SELECT COUNT(*) FROM bookmarks WHERE user_id = :uid"),
        {"uid": uid},
    ).scalar() or 0

    total_tags = db.execute(
        text("""
            SELECT COUNT(DISTINCT bt.tag_id)
            FROM bookmark_tags bt
            JOIN bookmarks b ON b.id = bt.bookmark_id
            WHERE b.user_id = :uid
        """),
        {"uid": uid},
    ).scalar() or 0

    top_tags_rows = db.execute(
        text("""
            SELECT t.name, COUNT(bt.bookmark_id) AS count
            FROM tags t
            JOIN bookmark_tags bt ON t.id = bt.tag_id
            JOIN bookmarks b ON b.id = bt.bookmark_id
            WHERE b.user_id = :uid
            GROUP BY t.id, t.name
            ORDER BY count DESC
            LIMIT 10
        """),
        {"uid": uid},
    ).fetchall()
    top_tags = [TagCount(name=row.name, count=row.count) for row in top_tags_rows]

    monthly_rows = db.execute(
        text("""
            SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS count
            FROM bookmarks
            WHERE user_id = :uid
            GROUP BY month
            ORDER BY month DESC
        """),
        {"uid": uid},
    ).fetchall()    
    bookmarks_per_month = [BookmarkPerMonth(month=row.month, count=row.count) for row in monthly_rows]
      
    return StatsResponse(
        total_bookmarks=total_bookmarks,
        total_tags=total_tags,
        top_tags=top_tags,
        bookmarks_per_month=bookmarks_per_month,
    )


@router.post("", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
def create_bookmark(
    body: BookmarkCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    bookmark = Bookmark(
        url=str(body.url),
        title=body.title,
        description=body.description,
        user_id=current_user.id,
        tags=_resolve_tags(body.tags, db),
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


@router.get("", response_model=PaginatedBookmarkResponse)
def list_bookmarks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    tag: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    from_date: Annotated[datetime | None, Query()] = None,
    to_date: Annotated[datetime | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    query = db.query(Bookmark).filter(Bookmark.user_id == current_user.id)

    if tag:
        query = query.join(Bookmark.tags).filter(Tag.name == tag.lower())
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            Bookmark.title.ilike(pattern) | Bookmark.description.ilike(pattern)
        )
    if from_date:
        query = query.filter(Bookmark.created_at >= from_date)
    if to_date:
        query = query.filter(Bookmark.created_at <= to_date)

    total = query.count()
    items = (
        query
        .options(selectinload(Bookmark.tags))
        .order_by(Bookmark.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedBookmarkResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{bookmark_id}", response_model=BookmarkResponse, responses={404: {**_error, "description": "Bookmark not found"}})
def get_bookmark(
    bookmark_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return _get_bookmark_or_404(bookmark_id, current_user, db)


@router.patch("/{bookmark_id}", response_model=BookmarkResponse, responses={404: {**_error, "description": "Bookmark not found"}})
def update_bookmark(
    bookmark_id: int,
    body: BookmarkUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    bookmark = _get_bookmark_or_404(bookmark_id, current_user, db)

    if body.url is not None:
        bookmark.url = str(body.url)
    if body.title is not None:
        bookmark.title = body.title
    if body.description is not None:
        bookmark.description = body.description
    if body.tags is not None:
        bookmark.tags = _resolve_tags(body.tags, db)

    db.commit()
    db.refresh(bookmark)
    return bookmark


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT, responses={404: {**_error, "description": "Bookmark not found"}})
def delete_bookmark(
    bookmark_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    bookmark = _get_bookmark_or_404(bookmark_id, current_user, db)
    db.delete(bookmark)
    db.commit()

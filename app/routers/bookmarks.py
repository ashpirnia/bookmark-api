from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Bookmark, Tag, User
from app.schemas import (
    BookmarkCreateRequest,
    BookmarkResponse,
    BookmarkUpdateRequest,
)

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])

# Implementing get-or-create pattern to handle many-to-many tag relationship 
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


def _get_bookmark(bookmark_id: int, user: User, db: Session) -> Bookmark:
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == user.id,
    ).first()
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    return bookmark


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


@router.get("", response_model=list[BookmarkResponse])
def list_bookmarks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return (
        db.query(Bookmark)
        .filter(Bookmark.user_id == current_user.id)
        .order_by(Bookmark.created_at.desc())
        .all()
    )


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
def get_bookmark(
    bookmark_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return _get_bookmark(bookmark_id, current_user, db)


@router.patch("/{bookmark_id}", response_model=BookmarkResponse)
def update_bookmark(
    bookmark_id: int,
    body: BookmarkUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    bookmark = _get_bookmark(bookmark_id, current_user, db)

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


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(
    bookmark_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    bookmark = _get_bookmark(bookmark_id, current_user, db)
    db.delete(bookmark)
    db.commit()

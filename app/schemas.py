from pydantic import BaseModel, EmailStr, Field, AnyHttpUrl

from datetime import datetime


class UserRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserResponse
    token: str
    

class TagResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class BookmarkCreateRequest(BaseModel):
    url: AnyHttpUrl
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    tags: list[str] = Field(default_factory=list)


class BookmarkUpdateRequest(BaseModel):
    url: AnyHttpUrl | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None


class BookmarkResponse(BaseModel):
    id: int
    url: str
    title: str
    description: str | None
    tags: list[TagResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
    

class PaginatedBookmarkResponse(BaseModel):
    items: list[BookmarkResponse]
    total: int
    page: int
    page_size: int


class TagCount(BaseModel):
    name: str
    count: int


class BookmarkPerMonth(BaseModel):
    month: str
    count: int


class StatsResponse(BaseModel):
    total_bookmarks: int
    total_tags: int
    top_tags: list[TagCount]
    bookmarks_per_month: list[BookmarkPerMonth]

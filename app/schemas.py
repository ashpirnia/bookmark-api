from datetime import datetime, timezone

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field, field_serializer


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


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


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

    @field_serializer("created_at", "updated_at")
    def _serialize_dt(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


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

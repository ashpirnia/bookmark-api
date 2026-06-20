from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas import (
    AuthResponse,
    ErrorResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

_error = {"model": ErrorResponse}

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {**_error, "description": "Email or username already taken"},
        422: {**_error, "description": "Validation error"},
    },
)
def register(
    body: UserRegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    db_user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return AuthResponse(user=UserResponse.model_validate(db_user), token=create_access_token(db_user.id))


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        401: {**_error, "description": "Invalid credentials"},
        422: {**_error, "description": "Validation error"},
    },
)
def login(
    body: UserLoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return AuthResponse(user=UserResponse.model_validate(user), token=create_access_token(user.id))

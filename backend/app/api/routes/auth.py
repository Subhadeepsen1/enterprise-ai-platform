"""Authentication routes: login, register, token refresh."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import Token, UserCreate, UserResponse
from app.services.auth_service import get_user_by_username, get_user_by_email

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=Token, summary="User Login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate a user and return a JWT access token."""
    user = await get_user_by_username(db, form_data.username)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    token = create_access_token(data={"sub": user.username, "role": user.role})
    logger.info(f"Successful login: {user.username} ({user.role})")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department,
        },
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register User")
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check for duplicates
    if await get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if await get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role or UserRole.EMPLOYEE,
        department=user_data.department,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"New user registered: {user.username} ({user.role})")
    return user


@router.get("/me", response_model=UserResponse, summary="Current User")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return current_user

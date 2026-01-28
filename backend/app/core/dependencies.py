"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Optional
from datetime import datetime

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.db import get_async_session
from app.models.user import User, APIKey, UserRole
from app.core.security import decode_access_token, hash_api_key
from app.schemas.user import TokenData


settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """Get the current authenticated user from JWT token."""
    if not token:
        return None
    
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    username: str = payload.get("sub")
    if username is None:
        return None
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    
    return user


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """Get current user and verify they are active."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user and verify they are an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


async def validate_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_async_session)
) -> Optional[APIKey]:
    """Validate API key from header."""
    if not x_api_key:
        return None
    
    # Hash the provided key
    key_hash = hash_api_key(x_api_key)
    
    # Find matching API key
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        )
    )
    api_key = result.scalar_one_or_none()
    
    if api_key is None:
        return None
    
    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None
    
    # Update usage stats
    api_key.last_used_at = datetime.utcnow()
    api_key.usage_count += 1
    await db.commit()
    
    return api_key


async def require_api_key_or_auth(
    current_user: Optional[User] = Depends(get_current_user),
    api_key: Optional[APIKey] = Depends(validate_api_key)
) -> tuple[Optional[User], Optional[APIKey]]:
    """Require either valid JWT or API key."""
    if current_user is None and api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required (JWT or API key)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return current_user, api_key


async def require_ingestion_permission(
    auth: tuple = Depends(require_api_key_or_auth)
) -> bool:
    """Verify ingestion permission."""
    user, api_key = auth
    
    # Users can always ingest
    if user is not None:
        return True
    
    # Check API key permission
    if api_key and api_key.can_ingest:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Ingestion permission required"
    )

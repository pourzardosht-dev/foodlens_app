import hashlib
import hmac
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Profile, ProfileToken
from app.db.session import get_db_session
from app.settings import Settings, get_settings


bearer_scheme = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[Session, Depends(get_db_session)]


def hash_token(token: str, pepper: str) -> bytes:
    return hmac.new(pepper.encode(), token.encode(), hashlib.sha256).digest()


def require_token_pepper(settings: Settings) -> str:
    if settings.token_pepper is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personal data service is not configured",
        )
    return settings.token_pepper.get_secret_value()


def get_current_profile(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: DatabaseSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Profile:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is required",
        )
    token_hash = hash_token(
        credentials.credentials, require_token_pepper(settings)
    )
    profile_token = session.scalar(
        select(ProfileToken).where(
            ProfileToken.token_hash == token_hash,
            ProfileToken.revoked_at.is_(None),
        )
    )
    if profile_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )
    profile = session.get(Profile, profile_token.profile_id)
    if profile is None or profile.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )
    profile_token.last_used_at = datetime.now(UTC)
    return profile


CurrentProfile = Annotated[Profile, Depends(get_current_profile)]
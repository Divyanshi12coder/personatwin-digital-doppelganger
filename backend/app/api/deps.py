from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import client_ip, limiter
from app.core.security import TokenError, decode_access_token
from app.db.session import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)

DB = Annotated[Session, Depends(get_db)]


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"}
    )


def get_current_user(
    db: DB,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (TokenError, ValueError) as exc:
        raise _unauthorized(str(exc) if isinstance(exc, TokenError) else "Invalid token") from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Account not found")
    if payload.get("ver") != user.token_version:
        raise _unauthorized("Session has been signed out, please sign in again")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def auth_rate_limit(request: Request) -> None:
    limiter.check(f"auth:{client_ip(request)}", get_settings().AUTH_RATE_LIMIT_PER_MINUTE)


def chat_rate_limit(request: Request, user: CurrentUser) -> None:
    limiter.check(f"chat:{user.id}", get_settings().CHAT_RATE_LIMIT_PER_MINUTE)

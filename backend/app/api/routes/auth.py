from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import DB, CurrentUser, auth_rate_limit
from app.core.security import create_access_token, hash_password, verify_password
from app.models import (
    Conversation,
    ConversationMemory,
    ExperienceMemory,
    KnowledgeDocument,
    MentorProfile,
    User,
    UserSettings,
)
from app.schemas.auth import (
    ChangePasswordRequest,
    DeleteAccountRequest,
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UpdateAccountRequest,
    UserOut,
)
from app.services.profile import get_or_create_personality, get_or_create_settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Verified against when the email is unknown, so login timing doesn't reveal which emails exist.
_DUMMY_HASH = hash_password("timing-equaliser-1")


def user_out(db: DB, user: User) -> UserOut:
    mentor = db.scalar(select(MentorProfile).where(MentorProfile.user_id == user.id))
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
        onboarding_completed=bool(mentor and mentor.onboarding_completed),
    )


def _token_response(db: DB, user: User) -> TokenResponse:
    token, expires_in = create_access_token(user.id, user.token_version)
    return TokenResponse(access_token=token, expires_in=expires_in, user=user_out(db, user))


@router.post(
    "/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(auth_rate_limit)]
)
def signup(body: SignupRequest, db: DB) -> TokenResponse:
    email = body.email.lower()
    if db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    user = User(email=email, full_name=body.full_name, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists") from exc
    get_or_create_personality(db, user)
    get_or_create_settings(db, user)
    db.commit()
    return _token_response(db, user)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(auth_rate_limit)])
def login(body: LoginRequest, db: DB) -> TokenResponse:
    user = db.scalar(select(User).where(func.lower(User.email) == body.email.lower()))
    if user is None:
        verify_password(body.password, _DUMMY_HASH)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not verify_password(body.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return _token_response(db, user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser, db: DB) -> UserOut:
    return user_out(db, user)


@router.patch("/me", response_model=UserOut)
def update_me(body: UpdateAccountRequest, user: CurrentUser, db: DB) -> UserOut:
    user.full_name = " ".join(body.full_name.split())
    db.commit()
    return user_out(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: CurrentUser, db: DB) -> Response:
    """Revoke every token issued so far for this account (signs out all devices)."""
    user.token_version += 1
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/change-password", response_model=TokenResponse, dependencies=[Depends(auth_rate_limit)])
def change_password(body: ChangePasswordRequest, user: CurrentUser, db: DB) -> TokenResponse:
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    user.token_version += 1  # other sessions are signed out; this one gets a fresh token
    db.commit()
    return _token_response(db, user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(auth_rate_limit)])
def delete_account(body: DeleteAccountRequest, user: CurrentUser, db: DB) -> Response:
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is incorrect")
    db.delete(user)  # cascades to every memory, conversation and setting
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/export")
def export_data(user: CurrentUser, db: DB) -> dict[str, Any]:
    """Download everything PersonaTwin stores about the account (embeddings excluded)."""
    mentor = db.scalar(select(MentorProfile).where(MentorProfile.user_id == user.id))
    personality = get_or_create_personality(db, user)
    settings = db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))

    def row(obj: Any, *fields: str) -> dict[str, Any]:
        return {f: getattr(obj, f) for f in fields}

    docs = db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.user_id == user.id)).all()
    exps = db.scalars(select(ExperienceMemory).where(ExperienceMemory.user_id == user.id)).all()
    mems = db.scalars(select(ConversationMemory).where(ConversationMemory.user_id == user.id)).all()
    convs = db.scalars(select(Conversation).where(Conversation.user_id == user.id)).all()
    return {
        "account": row(user, "email", "full_name", "created_at"),
        "mentor_profile": row(mentor, "mentor_name", "bio", "expertise_areas", "mentoring_domains") if mentor else None,
        "personality": {
            c.name: getattr(personality, c.name)
            for c in personality.__table__.columns
            if c.name not in ("id", "user_id")
        },
        "settings": {
            c.name: getattr(settings, c.name) for c in settings.__table__.columns if c.name not in ("id", "user_id")
        }
        if settings
        else None,
        "knowledge": [
            {**row(d, "title", "content", "category", "source_type", "source", "created_at"), "tags": [t.name for t in d.tags]}
            for d in docs
        ],
        "experiences": [
            {
                **row(
                    e,
                    "title",
                    "experience_type",
                    "situation",
                    "what_happened",
                    "lesson_learned",
                    "do_differently",
                    "context",
                    "occurred_on",
                    "importance",
                    "created_at",
                ),
                "tags": [t.name for t in e.tags],
            }
            for e in exps
        ],
        "conversation_memories": [row(m, "title", "content", "topic", "created_at") for m in mems],
        "conversations": [
            {
                **row(c, "title", "topic", "created_at"),
                "messages": [row(m, "role", "content", "created_at") for m in c.messages],
            }
            for c in convs
        ],
    }

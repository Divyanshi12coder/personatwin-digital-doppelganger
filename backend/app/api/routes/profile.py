from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.models import MentorProfile, PersonalityProfile, User
from app.schemas.profile import (
    MentorProfileIn,
    MentorProfileOut,
    OnboardingRequest,
    OptionItem,
    OptionsOut,
    PersonalityIn,
    PersonalityOut,
    ProfileOut,
    SettingsIn,
    SettingsOut,
)
from app.services.persona import EXPERIENCE_TYPES, KNOWLEDGE_CATEGORIES, MENTORING_DOMAINS, OPTIONS
from app.services.profile import get_mentor, get_or_create_personality, get_or_create_settings, profile_completeness

router = APIRouter(tags=["profile"])


def _profile_out(db: DB, user: User) -> ProfileOut:
    mentor = get_mentor(db, user)
    personality = get_or_create_personality(db, user)
    completeness, missing = profile_completeness(mentor, personality)
    return ProfileOut(
        mentor=MentorProfileOut.model_validate(mentor) if mentor else None,
        personality=PersonalityOut.model_validate(personality),
        completeness=completeness,
        missing=missing,
    )


def _apply_mentor(db: DB, user: User, body: MentorProfileIn) -> MentorProfile:
    mentor = get_mentor(db, user)
    if mentor is None:
        mentor = MentorProfile(user_id=user.id, mentor_name=body.mentor_name)
        db.add(mentor)
    for field, value in body.model_dump().items():
        setattr(mentor, field, value)
    return mentor


def _apply_personality(db: DB, user: User, body: PersonalityIn) -> PersonalityProfile:
    personality = get_or_create_personality(db, user)
    for field, value in body.model_dump().items():
        setattr(personality, field, value)
    return personality


@router.get("/profile/options", response_model=OptionsOut)
def options() -> OptionsOut:
    return OptionsOut(
        persona={k: [OptionItem(value=v, description=d) for v, d in opts.items()] for k, opts in OPTIONS.items()},
        experience_types=[OptionItem(value=k, description=v) for k, v in EXPERIENCE_TYPES.items()],
        knowledge_categories=[OptionItem(value=k, description=v) for k, v in KNOWLEDGE_CATEGORIES.items()],
        mentoring_domains=MENTORING_DOMAINS,
    )


@router.get("/profile", response_model=ProfileOut)
def get_profile(user: CurrentUser, db: DB) -> ProfileOut:
    out = _profile_out(db, user)
    db.commit()  # persists a default personality row the first time
    return out


@router.post("/profile/onboarding", response_model=ProfileOut)
def complete_onboarding(body: OnboardingRequest, user: CurrentUser, db: DB) -> ProfileOut:
    mentor = _apply_mentor(db, user, body.mentor)
    mentor.onboarding_completed = True
    _apply_personality(db, user, body.personality)
    db.commit()
    return _profile_out(db, user)


@router.put("/profile/mentor", response_model=ProfileOut)
def update_mentor(body: MentorProfileIn, user: CurrentUser, db: DB) -> ProfileOut:
    _apply_mentor(db, user, body)
    db.commit()
    return _profile_out(db, user)


@router.put("/profile/personality", response_model=ProfileOut)
def update_personality(body: PersonalityIn, user: CurrentUser, db: DB) -> ProfileOut:
    _apply_personality(db, user, body)
    db.commit()
    return _profile_out(db, user)


@router.get("/settings", response_model=SettingsOut)
def get_user_settings(user: CurrentUser, db: DB) -> SettingsOut:
    row = get_or_create_settings(db, user)
    db.commit()
    return SettingsOut.model_validate(row)


@router.put("/settings", response_model=SettingsOut)
def update_user_settings(body: SettingsIn, user: CurrentUser, db: DB) -> SettingsOut:
    row = get_or_create_settings(db, user)
    for field, value in body.model_dump().items():
        setattr(row, field, value)
    db.commit()
    return SettingsOut.model_validate(row)

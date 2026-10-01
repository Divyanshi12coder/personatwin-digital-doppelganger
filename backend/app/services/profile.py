"""Helpers for the per-user singleton rows (mentor profile, personality, settings)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MentorProfile, PersonalityProfile, User, UserSettings
from app.services.persona import PersonaSnapshot


def get_or_create_personality(db: Session, user: User) -> PersonalityProfile:
    row = db.scalar(select(PersonalityProfile).where(PersonalityProfile.user_id == user.id))
    if row is None:
        row = PersonalityProfile(user_id=user.id, values=[], signature_phrases=[])
        db.add(row)
        db.flush()
    return row


def get_or_create_settings(db: Session, user: User) -> UserSettings:
    row = db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    if row is None:
        row = UserSettings(user_id=user.id)
        db.add(row)
        db.flush()
    return row


def get_mentor(db: Session, user: User) -> MentorProfile | None:
    return db.scalar(select(MentorProfile).where(MentorProfile.user_id == user.id))


def persona_snapshot(db: Session, user: User) -> PersonaSnapshot:
    mentor = get_mentor(db, user)
    p = get_or_create_personality(db, user)
    return PersonaSnapshot(
        mentor_name=mentor.mentor_name if mentor else f"{user.full_name.split(' ')[0]}'s Twin",
        bio=mentor.bio if mentor else "",
        expertise_areas=list(mentor.expertise_areas) if mentor else [],
        mentoring_domains=list(mentor.mentoring_domains) if mentor else [],
        communication_style=p.communication_style,
        tone=p.tone,
        teaching_approach=p.teaching_approach,
        decision_style=p.decision_style,
        encouragement_style=p.encouragement_style,
        response_length=p.response_length,
        formality=p.formality,
        directness=p.directness,
        warmth=p.warmth,
        humor=p.humor,
        values=list(p.values),
        signature_phrases=list(p.signature_phrases),
        philosophy_encouragement=p.philosophy_encouragement,
        philosophy_mistakes=p.philosophy_mistakes,
        philosophy_decisions=p.philosophy_decisions,
        philosophy_teaching=p.philosophy_teaching,
        boundaries=p.boundaries,
    )


def profile_completeness(mentor: MentorProfile | None, p: PersonalityProfile) -> tuple[int, list[str]]:
    """Percentage of the persona the user has filled in, plus what's missing."""
    checks: list[tuple[str, bool]] = [
        ("Mentor name", bool(mentor and mentor.mentor_name.strip())),
        ("Short bio", bool(mentor and len(mentor.bio.strip()) >= 20)),
        ("Expertise areas", bool(mentor and mentor.expertise_areas)),
        ("Mentoring domains", bool(mentor and mentor.mentoring_domains)),
        ("Values", bool(p.values)),
        ("How you encourage people", bool(p.philosophy_encouragement.strip())),
        ("How you handle mistakes", bool(p.philosophy_mistakes.strip())),
        ("How you approach hard decisions", bool(p.philosophy_decisions.strip())),
        ("How you teach", bool(p.philosophy_teaching.strip())),
    ]
    done = sum(1 for _, ok in checks if ok)
    return round(100 * done / len(checks)), [label for label, ok in checks if not ok]

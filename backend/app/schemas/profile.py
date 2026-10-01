from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel, ShortList
from app.services.persona import OPTIONS


def _option(key: str):  # type: ignore[no-untyped-def]
    def check(cls: type, v: str) -> str:
        if v not in OPTIONS[key]:
            raise ValueError(f"must be one of: {', '.join(OPTIONS[key])}")
        return v

    return field_validator(key)(classmethod(check))  # type: ignore[arg-type]


class MentorProfileIn(BaseModel):
    mentor_name: str = Field(min_length=1, max_length=80)
    bio: str = Field(default="", max_length=2000)
    expertise_areas: ShortList
    mentoring_domains: ShortList

    @field_validator("mentor_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("Mentor name is required")
        return v


class MentorProfileOut(ORMModel):
    mentor_name: str
    bio: str
    expertise_areas: list[str]
    mentoring_domains: list[str]
    onboarding_completed: bool
    updated_at: datetime


class PersonalityIn(BaseModel):
    communication_style: str = "warm"
    tone: str = "encouraging"
    teaching_approach: str = "examples_first"
    decision_style: str = "analytical"
    encouragement_style: str = "celebrate_progress"
    response_length: str = "balanced"
    formality: int = Field(default=40, ge=0, le=100)
    directness: int = Field(default=60, ge=0, le=100)
    warmth: int = Field(default=70, ge=0, le=100)
    humor: int = Field(default=30, ge=0, le=100)
    values: ShortList
    signature_phrases: ShortList
    philosophy_encouragement: str = Field(default="", max_length=2000)
    philosophy_mistakes: str = Field(default="", max_length=2000)
    philosophy_decisions: str = Field(default="", max_length=2000)
    philosophy_teaching: str = Field(default="", max_length=2000)
    boundaries: str = Field(default="", max_length=1000)

    check_communication_style = _option("communication_style")
    check_tone = _option("tone")
    check_teaching_approach = _option("teaching_approach")
    check_decision_style = _option("decision_style")
    check_encouragement_style = _option("encouragement_style")
    check_response_length = _option("response_length")


class PersonalityOut(ORMModel):
    communication_style: str
    tone: str
    teaching_approach: str
    decision_style: str
    encouragement_style: str
    response_length: str
    formality: int
    directness: int
    warmth: int
    humor: int
    values: list[str]
    signature_phrases: list[str]
    philosophy_encouragement: str
    philosophy_mistakes: str
    philosophy_decisions: str
    philosophy_teaching: str
    boundaries: str
    updated_at: datetime


class OnboardingRequest(BaseModel):
    mentor: MentorProfileIn
    personality: PersonalityIn


class ProfileOut(BaseModel):
    mentor: MentorProfileOut | None
    personality: PersonalityOut
    completeness: int
    missing: list[str]


class SettingsIn(BaseModel):
    save_conversations: bool = True
    use_conversation_memory: bool = True
    auto_remember: bool = False
    retrieval_top_k: int = Field(default=6, ge=1, le=12)
    min_relevance: float = Field(default=0.12, ge=0.0, le=0.9)
    creativity: float = Field(default=0.5, ge=0.0, le=1.0)
    show_sources: bool = True


class SettingsOut(ORMModel, SettingsIn):
    pass


class OptionItem(BaseModel):
    value: str
    description: str


class OptionsOut(BaseModel):
    persona: dict[str, list[OptionItem]]
    experience_types: list[OptionItem]
    knowledge_categories: list[OptionItem]
    mentoring_domains: list[str]

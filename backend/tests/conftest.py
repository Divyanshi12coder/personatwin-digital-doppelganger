import os

# Configure the app for tests *before* it is imported.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ENVIRONMENT"] = "test"
os.environ["AI_PROVIDER"] = "demo"
os.environ["EMBEDDING_PROVIDER"] = "local"
os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret-123"

from collections.abc import Generator, Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


# Set TEST_DATABASE_URL (e.g. postgresql+psycopg://user:pw@localhost/pt_test) to run the
# whole suite against PostgreSQL + pgvector instead of in-memory SQLite.
TEST_DATABASE_URL = Settings.normalize_db_url(os.environ.get("TEST_DATABASE_URL", ""))


@pytest.fixture()
def engine() -> Iterator[object]:
    if TEST_DATABASE_URL:
        eng = create_engine(TEST_DATABASE_URL)
        with eng.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.drop_all(eng)
        Base.metadata.create_all(eng)
        yield eng
        Base.metadata.drop_all(eng)
        eng.dispose()
        return

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(eng, "connect")
    def _fk(dbapi_conn, _):  # type: ignore[no-untyped-def]
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine) -> Iterator[Session]:  # type: ignore[no-untyped-def]
    SessionTest = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = SessionTest()
    yield session
    session.close()


@pytest.fixture()
def client(engine) -> Generator[TestClient, None, None]:  # type: ignore[no-untyped-def]
    SessionTest = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Iterator[Session]:
        db = SessionTest()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    limiter.reset()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    limiter.reset()


def signup(client: TestClient, email: str = "ada@example.com", name: str = "Ada Lovelace") -> dict[str, str]:
    res = client.post("/api/auth/signup", json={"email": email, "full_name": name, "password": "analytical1"})
    assert res.status_code == 201, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture()
def auth(client: TestClient) -> dict[str, str]:
    return signup(client)


ONBOARDING = {
    "mentor": {
        "mentor_name": "Ada's Twin",
        "bio": "Engineer turned teacher who loves helping people learn hard things patiently.",
        "expertise_areas": ["Software engineering", "Teaching"],
        "mentoring_domains": ["Career development", "Learning"],
    },
    "personality": {
        "communication_style": "warm",
        "tone": "encouraging",
        "teaching_approach": "step_by_step",
        "decision_style": "experimental",
        "encouragement_style": "celebrate_progress",
        "response_length": "balanced",
        "formality": 30,
        "directness": 65,
        "warmth": 80,
        "humor": 20,
        "values": ["Curiosity", "Honesty"],
        "signature_phrases": ["Small experiments beat big guesses."],
        "philosophy_encouragement": "Notice progress out loud.",
        "philosophy_mistakes": "Mistakes are data.",
        "philosophy_decisions": "Make reversible bets first.",
        "philosophy_teaching": "Show, then let them try.",
        "boundaries": "",
    },
}


def onboard(client: TestClient, headers: dict[str, str]) -> None:
    res = client.post("/api/profile/onboarding", json=ONBOARDING, headers=headers)
    assert res.status_code == 200, res.text


CAREER_EXPERIENCE = {
    "title": "Leaving my stable bank job to become a software engineer",
    "experience_type": "career",
    "situation": "I had worked in banking for six years and felt stuck, but switching careers felt risky.",
    "what_happened": "I spent six months building small projects at night before I resigned and took a junior role.",
    "lesson_learned": "Test a career change with small experiments before you jump, and keep a financial runway.",
    "do_differently": "I would have talked to more engineers before quitting instead of guessing what the job was like.",
    "context": "2016, London",
    "importance": 5,
    "tags": ["career change", "risk"],
}

LEARNING_NOTE = {
    "title": "How I learn hard topics",
    "content": (
        "Spaced repetition beats cramming. Review material after one day, three days and a week.\n\n"
        "Active recall: close the book and explain the idea from memory before re-reading it.\n\n"
        "Teaching a concept to someone else exposes gaps in understanding immediately."
    ),
    "category": "learning",
    "tags": ["study", "memory"],
}

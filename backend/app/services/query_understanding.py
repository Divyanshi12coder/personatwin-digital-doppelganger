"""Step 1 of the chat pipeline: understand the user's query.

Deterministic and cheap (no LLM call): classifies the mentoring topic and intent,
extracts keywords, and detects whether the user is asking about the mentor's own
experiences — in which case grounding in *episodic* memory matters most.
"""

import re
from dataclasses import dataclass, field

from app.services.embeddings import stem, tokenize

TOPICS: dict[str, tuple[str, ...]] = {
    "career": ("career", "job", "role", "promotion", "interview", "resume", "salary", "employer", "industry", "profession", "hire", "quit", "manager", "workplace", "offer"),
    "learning": ("learn", "study", "course", "skill", "exam", "read", "book", "practice", "understand", "school", "university", "tutorial", "language"),
    "productivity": ("productive", "productivity", "focus", "procrastinate", "procrastination", "habit", "routine", "time", "schedule", "distract", "deadline", "energy", "burnout"),
    "decision_making": ("decide", "decision", "choose", "choice", "option", "should", "whether", "tradeoff", "pros", "cons", "dilemma"),
    "goal_setting": ("goal", "plan", "milestone", "resolution", "target", "ambition", "vision", "objective", "roadmap"),
    "problem_solving": ("problem", "stuck", "bug", "fix", "solve", "issue", "blocked", "debug", "obstacle", "approach"),
    "personal_development": ("confidence", "growth", "mindset", "motivation", "fear", "anxious", "self", "improve", "resilience", "imposter", "values", "purpose"),
    "leadership": ("lead", "team", "leader", "delegate", "manage", "feedback", "mentor", "conflict", "stakeholder", "report"),
    "creativity": ("creative", "design", "write", "writing", "art", "idea", "portfolio", "craft", "inspiration"),
}

TOPIC_LABELS = {
    "career": "Career",
    "learning": "Learning",
    "productivity": "Productivity",
    "decision_making": "Decision-making",
    "goal_setting": "Goal setting",
    "problem_solving": "Problem solving",
    "personal_development": "Personal development",
    "leadership": "Leadership",
    "creativity": "Creativity",
    "general": "General",
}

_PERSONAL_PATTERNS = re.compile(
    r"\b(have you ever|did you ever|when you were|your (own )?experience|what did you do|"
    r"tell me about (a|the) time|what would you do|how did you|your story|you once)\b",
    re.IGNORECASE,
)
_GREETING = re.compile(r"^\s*(hi|hello|hey|good (morning|afternoon|evening)|thanks|thank you)\b[\s!.,]*$", re.I)


@dataclass
class QueryAnalysis:
    text: str
    topic: str
    topic_label: str
    intent: str  # advice|decision|learning|reflection|personal|smalltalk|question
    keywords: list[str] = field(default_factory=list)
    asks_personal_experience: bool = False


def _topic_scores(stems: set[str]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for topic, words in TOPICS.items():
        score = sum(1 for w in words if stem(w) in stems)
        if score:
            scores[topic] = score
    return scores


def analyze_query(text: str, previous_topic: str | None = None) -> QueryAnalysis:
    words = tokenize(text)
    stems = {stem(w) for w in words} | set(words)
    scores = _topic_scores(stems)
    if scores:
        topic = max(scores.items(), key=lambda kv: (kv[1], kv[0] == previous_topic))[0]
    else:
        topic = previous_topic or "general"

    lowered = text.lower()
    personal = bool(_PERSONAL_PATTERNS.search(text))
    if _GREETING.match(text):
        intent = "smalltalk"
    elif personal:
        intent = "personal"
    elif "decision_making" in scores or re.search(r"\b(should i|whether|or not)\b", lowered):
        intent = "decision"
    elif "learning" in scores and re.search(r"\b(how (do|can|should) i learn|study|understand)\b", lowered):
        intent = "learning"
    elif re.search(r"\b(feel|feeling|struggl|afraid|worried|stuck)\w*", lowered):
        intent = "reflection"
    elif "?" in text or re.match(r"^\s*(how|what|why|when|where|which|can|could|is|are)\b", lowered):
        intent = "question"
    else:
        intent = "advice"

    seen: list[str] = []
    for w in words:
        if len(w) > 2 and w not in seen:
            seen.append(w)
    return QueryAnalysis(
        text=text,
        topic=topic,
        topic_label=TOPIC_LABELS[topic],
        intent=intent,
        keywords=seen[:12],
        asks_personal_experience=personal,
    )

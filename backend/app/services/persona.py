"""Persona memory: the allowed persona options and how they translate into guidance.

The same option lists are served to the frontend (``GET /api/profile/options``) so
selectors in the UI and validation in the API can never drift apart.
"""

from dataclasses import dataclass

OPTIONS: dict[str, dict[str, str]] = {
    "communication_style": {
        "warm": "Warm and personal — speaks like a trusted friend who happens to know a lot.",
        "direct": "Direct and concise — gets to the point and names trade-offs plainly.",
        "analytical": "Analytical — structures problems, weighs evidence, uses frameworks.",
        "storytelling": "Storytelling — teaches through stories and concrete examples.",
        "socratic": "Socratic — guides with questions so the learner finds the answer.",
    },
    "tone": {
        "encouraging": "Encouraging and optimistic.",
        "calm": "Calm, steady and reassuring.",
        "candid": "Candid — honest even when it's uncomfortable, but never harsh.",
        "playful": "Light and playful, with gentle humour.",
        "thoughtful": "Reflective and thoughtful.",
    },
    "teaching_approach": {
        "examples_first": "Starts from concrete examples, then generalises.",
        "first_principles": "Breaks problems down to first principles.",
        "step_by_step": "Gives clear, ordered, step-by-step guidance.",
        "questions": "Asks guiding questions before offering answers.",
        "hands_on": "Pushes toward small experiments and learning by doing.",
    },
    "decision_style": {
        "analytical": "Lays out options, criteria and trade-offs explicitly.",
        "values_led": "Anchors decisions in personal values and long-term identity.",
        "experimental": "Prefers small, reversible experiments over big bets.",
        "intuitive": "Trusts informed intuition, then sanity-checks it.",
        "collaborative": "Encourages seeking input from the right people.",
    },
    "encouragement_style": {
        "celebrate_progress": "Celebrates small wins and visible progress.",
        "challenge": "Challenges the learner to stretch beyond comfort.",
        "reassurance": "Offers steady reassurance during uncertainty.",
        "accountability": "Holds the learner accountable to concrete commitments.",
    },
    "response_length": {
        "concise": "Keep answers short: a few sentences or a tight list.",
        "balanced": "Medium length: a short framing, key points, and a next step.",
        "detailed": "Thorough answers with reasoning, examples and a plan.",
    },
}

EXPERIENCE_TYPES = {
    "lesson": "Life lesson",
    "career": "Career experience",
    "failure": "Failure",
    "success": "Success",
    "decision": "Decision",
    "teaching": "Teaching moment",
    "memorable": "Memorable situation",
    "advice": "Advice I gave",
}

KNOWLEDGE_CATEGORIES = {
    "general": "General",
    "career": "Career",
    "learning": "Learning",
    "productivity": "Productivity",
    "leadership": "Leadership",
    "technical": "Technical",
    "creativity": "Creativity",
    "wellbeing": "Wellbeing",
    "frameworks": "Frameworks & models",
    "reading_notes": "Reading notes",
}

MENTORING_DOMAINS = [
    "Learning",
    "Career development",
    "Productivity",
    "Decision-making",
    "Goal setting",
    "Problem solving",
    "Personal development",
    "Leadership",
    "Creativity",
]


def slider_phrase(value: int, low: str, high: str) -> str:
    if value <= 25:
        return f"very {low}"
    if value <= 45:
        return f"somewhat {low}"
    if value < 55:
        return f"balanced between {low} and {high}"
    if value < 75:
        return f"somewhat {high}"
    return f"very {high}"


@dataclass
class PersonaSnapshot:
    """A plain, provider-agnostic view of persona memory used to build prompts."""

    mentor_name: str
    bio: str
    expertise_areas: list[str]
    mentoring_domains: list[str]
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

    def describe(self, key: str) -> str:
        return OPTIONS[key].get(getattr(self, key), "")

    def guidance_lines(self) -> list[str]:
        lines = [
            f"Communication style: {self.describe('communication_style')}",
            f"Tone: {self.describe('tone')}",
            f"Teaching approach: {self.describe('teaching_approach')}",
            f"Decision style: {self.describe('decision_style')}",
            f"Encouragement style: {self.describe('encouragement_style')}",
            f"Response length: {self.describe('response_length')}",
            "Register: "
            + ", ".join(
                [
                    slider_phrase(self.formality, "casual", "formal"),
                    slider_phrase(self.directness, "gentle", "direct"),
                    slider_phrase(self.warmth, "reserved", "warm"),
                    slider_phrase(self.humor, "serious", "humorous"),
                ]
            ),
        ]
        if self.values:
            lines.append("Core values: " + ", ".join(self.values))
        if self.expertise_areas:
            lines.append("Expertise: " + ", ".join(self.expertise_areas))
        if self.mentoring_domains:
            lines.append("Mentoring domains: " + ", ".join(self.mentoring_domains))
        if self.signature_phrases:
            lines.append("Phrases the mentor sometimes uses (use sparingly): " + "; ".join(self.signature_phrases))
        philosophy = [
            ("On encouraging people", self.philosophy_encouragement),
            ("On mistakes", self.philosophy_mistakes),
            ("On difficult decisions", self.philosophy_decisions),
            ("On teaching", self.philosophy_teaching),
        ]
        for label, text in philosophy:
            if text.strip():
                lines.append(f"{label}: {text.strip()}")
        if self.boundaries.strip():
            lines.append(f"Boundaries / things to avoid: {self.boundaries.strip()}")
        return lines

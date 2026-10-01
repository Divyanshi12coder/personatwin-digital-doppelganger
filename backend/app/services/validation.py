"""Response validation — the last gate before a reply reaches the user.

* removes citation labels that don't match a retrieved memory (hallucinated cites)
* detects first-person memory claims that no experience memory supports and
  appends a transparent note instead of letting a fabricated "memory" stand
* strips any leaked internal markup
* classifies grounding: grounded / partial / ungrounded
"""

import re
from dataclasses import dataclass, field

from app.services.context import AssembledContext

CITATION_RE = re.compile(r"\[([KEC]\d{1,2})\]")
_LEAK_RE = re.compile(r"</?(memory_context|analysis)>", re.IGNORECASE)
MEMORY_CLAIM_RE = re.compile(
    r"\b(I remember|I recall|I once|when I was|back when I|(in|from) my (own )?experience|"
    r"years ago,? I|I've been through|I went through|my own (story|journey)|"
    r"(early|later|earlier) in my (career|life)|in my (first|last|previous|old) (job|role|company|team)|"
    r"I learned the hard way|I (got|was) (fired|promoted|laid off|rejected)|"
    r"I (quit|left|switched|changed|failed|lost)\b|when I (quit|left|joined|started|moved|switched|was)\b)",
    re.IGNORECASE,
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_EXPERIENCE_CITE_RE = re.compile(r"\[E\d{1,2}\]")
UNSUPPORTED_MEMORY_NOTE = (
    "_Transparency note: I don't have a recorded experience that matches this, so please treat any "
    "personal-sounding phrasing above as general guidance rather than a real memory._"
)


class EmptyResponseError(ValueError):
    pass


@dataclass
class ValidatedResponse:
    text: str
    cited_labels: list[str] = field(default_factory=list)
    removed_labels: list[str] = field(default_factory=list)
    grounding: str = "ungrounded"
    unsupported_memory_claim: bool = False


def _has_unsupported_claim(text: str) -> bool:
    """A first-person memory claim must carry an experience citation ([E#]) in the
    same sentence or the one right after it; one citation elsewhere in the reply
    doesn't vouch for every story in it."""
    sentences = [s for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    for i, sentence in enumerate(sentences):
        if MEMORY_CLAIM_RE.search(sentence) and not _EXPERIENCE_CITE_RE.search(" ".join(sentences[i : i + 2])):
            return True
    return False


def validate_response(raw: str, context: AssembledContext) -> ValidatedResponse:
    text = _LEAK_RE.sub("", raw or "").strip()
    if not text:
        raise EmptyResponseError("The AI provider returned an empty response")

    allowed = context.labels
    cited: list[str] = []
    removed: list[str] = []

    def _check(match: re.Match[str]) -> str:
        label = match.group(1)
        if label in allowed:
            if label not in cited:
                cited.append(label)
            return match.group(0)
        removed.append(label)
        return ""

    text = CITATION_RE.sub(_check, text)
    text = re.sub(r"[ \t]+([.,;:!?])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    unsupported = _has_unsupported_claim(text)
    if unsupported:
        text = f"{text}\n\n{UNSUPPORTED_MEMORY_NOTE}"

    if not context.items:
        grounding = "ungrounded"
    elif cited:
        grounding = "grounded"
    else:
        grounding = "partial"
    return ValidatedResponse(
        text=text,
        cited_labels=cited,
        removed_labels=removed,
        grounding=grounding,
        unsupported_memory_claim=unsupported,
    )

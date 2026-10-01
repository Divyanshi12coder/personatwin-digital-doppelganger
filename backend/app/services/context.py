"""Context assembly: turn retrieved memories into labelled, budgeted context.

Each memory gets a stable citation label — ``K#`` knowledge, ``E#`` experience,
``C#`` past conversation — that the model must use when it relies on it. Labels
are what response validation later checks against.
"""

import re
from dataclasses import dataclass

from app.services.retrieval import (
    SOURCE_CONVERSATION,
    SOURCE_EXPERIENCE,
    SOURCE_KNOWLEDGE,
    RetrievalResult,
    RetrievedMemory,
)

PREFIX = {SOURCE_KNOWLEDGE: "K", SOURCE_EXPERIENCE: "E", SOURCE_CONVERSATION: "C"}
MAX_CONTEXT_CHARS = 9000
MAX_ITEM_CHARS = 1600


@dataclass
class ContextItem:
    label: str
    memory: RetrievedMemory


@dataclass
class AssembledContext:
    items: list[ContextItem]
    text: str

    @property
    def labels(self) -> set[str]:
        return {i.label for i in self.items}

    def by_type(self, source_type: str) -> list[ContextItem]:
        return [i for i in self.items if i.memory.source_type == source_type]


_FRAMING_TAG_RE = re.compile(r"</?\s*(memory_context|analysis)\b[^>]*>", re.IGNORECASE)


def neutralize_framing(text: str) -> str:
    """Remove our prompt-framing tags from user-controlled text so imported content
    can't close <memory_context> early and smuggle instructions outside it."""
    return _FRAMING_TAG_RE.sub("", text)


def _clip(text: str, limit: int) -> str:
    text = neutralize_framing(text).strip()
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def _render(item: ContextItem) -> str:
    m = item.memory
    title = neutralize_framing(m.title)
    if m.source_type == SOURCE_EXPERIENCE:
        d = m.details
        fields = [
            ("Situation", d.get("situation", "")),
            ("What happened", d.get("what_happened", "")),
            ("What I learned", d.get("lesson_learned", "")),
            ("What I'd do differently", d.get("do_differently", "")),
            ("Context", d.get("context", "")),
            ("When", d.get("occurred_on") or ""),
        ]
        body = "\n".join(f"  {k}: {_clip(v, 500)}" for k, v in fields if v)
        return f"[{item.label}] Experience ({m.category}) — \"{title}\" (relevance {m.score:.2f})\n{body}"
    if m.source_type == SOURCE_CONVERSATION:
        return (
            f"[{item.label}] Past mentor conversation note — \"{title}\" (relevance {m.score:.2f}). "
            f"Partly AI-generated; NOT a lived experience.\n  {_clip(m.content, MAX_ITEM_CHARS)}"
        )
    return (
        f"[{item.label}] Knowledge note ({m.category}) — \"{title}\" (relevance {m.score:.2f})\n"
        f"  {_clip(m.content, MAX_ITEM_CHARS)}"
    )


def assemble_context(result: RetrievalResult, max_chars: int = MAX_CONTEXT_CHARS) -> AssembledContext:
    items: list[ContextItem] = []
    counters = {k: 0 for k in PREFIX}
    # Interleave by score so the budget favours the most relevant memories overall.
    for memory in sorted(result.all, key=lambda m: m.score, reverse=True):
        counters[memory.source_type] += 1
        items.append(ContextItem(f"{PREFIX[memory.source_type]}{counters[memory.source_type]}", memory))

    rendered: list[str] = []
    kept: list[ContextItem] = []
    used = 0
    for item in items:
        block = _render(item)
        if used + len(block) > max_chars and kept:
            break
        rendered.append(block)
        kept.append(item)
        used += len(block)
    return AssembledContext(items=kept, text="\n\n".join(rendered))

"""Paragraph-aware text chunking for knowledge documents.

Paragraphs are packed greedily up to ``chunk_size`` characters. A paragraph longer
than the limit is split on sentence boundaries, and as a last resort on raw
characters. Consecutive chunks share ``overlap`` characters of trailing context so
that an idea spanning a boundary is still retrievable.
"""

import re

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _split_long(paragraph: str, size: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_RE.split(paragraph):
        while len(sentence) > size:  # pathological sentence with no punctuation
            if current:
                pieces.append(current)
                current = ""
            pieces.append(sentence[:size])
            sentence = sentence[size:]
        if current and len(current) + 1 + len(sentence) > size:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    units: list[str] = []
    for p in paragraphs:
        units.extend(_split_long(p, chunk_size) if len(p) > chunk_size else [p])

    chunks: list[str] = []
    current = ""
    for unit in units:
        if current and len(current) + 2 + len(unit) > chunk_size:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            # Start the overlap at a word boundary to keep it readable.
            if tail and " " in tail:
                tail = tail[tail.index(" ") + 1 :]
            current = f"{tail}\n\n{unit}".strip() if tail else unit
        else:
            current = f"{current}\n\n{unit}".strip() if current else unit
    if current:
        chunks.append(current)
    return chunks


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.split(text.replace("\n", " ")) if len(s.strip()) > 2]

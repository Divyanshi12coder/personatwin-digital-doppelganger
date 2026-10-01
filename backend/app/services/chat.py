"""Chat orchestration — the core mentor pipeline.

    User query
      -> 1. query understanding          (topic, intent, personal-experience check)
      -> 2. memory retrieval             (knowledge + experiences + conversation notes, user-scoped)
      -> 3. persona memory               (communication profile + philosophy)
      -> 4. context assembly             (labelled, budgeted memory context)
      -> 5. prompt construction          (system prompt + short-term history + context)
      -> 6. LLM generation               (provider abstraction, demo fallback)
      -> 7. response validation          (citations, fabricated-memory guard, grounding)
      -> 8. optional persistence         (messages, sources, opt-in conversation memory)

The LLM is never the source of truth for memories: everything personal it may say
comes from rows retrieved for *this* user in step 2.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import utcnow
from app.models import Conversation, ConversationMemory, Message, MessageSource, User, UserSettings
from app.services.ai import AIProviderError, GenerationRequest, get_ai_service
from app.services.chunking import split_sentences
from app.services.context import AssembledContext, assemble_context
from app.services.embeddings import EmbeddingError
from app.services.indexing import index_conversation_memory
from app.services.profile import get_or_create_settings, persona_snapshot
from app.services.prompts import build_system_prompt, build_user_turn
from app.services.query_understanding import QueryAnalysis, analyze_query
from app.services.retrieval import RetrievalResult, retrieve
from app.services.validation import CITATION_RE, EmptyResponseError, validate_response


# Memories scoring below this fraction of the best match are left out of the prompt.
RELATIVE_CUTOFF = 0.55


@dataclass
class SourceRef:
    label: str
    source_type: str
    source_id: int
    title: str
    snippet: str
    score: float
    cited: bool


@dataclass
class PipelineResult:
    text: str
    grounding: str
    analysis: QueryAnalysis
    sources: list[SourceRef]
    provider: str
    model: str
    latency_ms: int
    trace: dict[str, Any]
    notice: str | None = None
    degraded: bool = False


@dataclass
class HistoryTurn:
    role: str
    content: str


@dataclass
class ExchangeResult:
    conversation: Conversation | None
    user_message: Message | None
    assistant_message: Message | None
    pipeline: PipelineResult
    persisted: bool
    remembered_id: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def _clean_history(turns: list[HistoryTurn], limit: int) -> list[dict[str, str]]:
    """Short-term memory: the last ``limit`` turns, citation labels stripped
    (labels are per-reply and would be ambiguous across turns), roles alternating."""
    cleaned: list[dict[str, str]] = []
    for turn in turns[-limit:]:
        if turn.role not in ("user", "assistant") or not turn.content.strip():
            continue
        text = CITATION_RE.sub("", turn.content).strip()
        if cleaned and cleaned[-1]["role"] == turn.role:
            cleaned[-1]["content"] += "\n\n" + text
        else:
            cleaned.append({"role": turn.role, "content": text})
    while cleaned and cleaned[0]["role"] != "user":
        cleaned.pop(0)
    while cleaned and cleaned[-1]["role"] == "user":
        cleaned.pop()  # the new user turn is appended separately
    return cleaned


def run_pipeline(
    db: Session,
    user: User,
    query: str,
    history: list[HistoryTurn],
    user_settings: UserSettings,
    previous_topic: str | None = None,
) -> PipelineResult:
    settings = get_settings()
    started = time.perf_counter()
    steps: list[dict[str, Any]] = []

    def mark(step: str, t0: float, detail: str) -> None:
        steps.append({"step": step, "ms": int((time.perf_counter() - t0) * 1000), "detail": detail})

    t = time.perf_counter()
    analysis = analyze_query(query, previous_topic)
    mark("understand", t, f"{analysis.topic_label} · {analysis.intent}")

    t = time.perf_counter()
    retrieval_notice: str | None = None
    if analysis.intent == "smalltalk":
        retrieval = RetrievalResult([], [], [], {})
    else:
        try:
            retrieval = retrieve(
                db,
                user.id,
                query,
                top_k=user_settings.retrieval_top_k,
                min_relevance=user_settings.min_relevance,
                include_conversations=user_settings.use_conversation_memory,
                relative_cutoff=RELATIVE_CUTOFF,
            )
        except EmbeddingError:
            retrieval = RetrievalResult([], [], [], {})
            retrieval_notice = (
                "Memory search is temporarily unavailable (the embedding provider could not be reached), "
                "so this answer could not draw on your memories."
            )
    mark(
        "retrieve",
        t,
        f"{len(retrieval.knowledge)} knowledge · {len(retrieval.experiences)} experiences · "
        f"{len(retrieval.conversations)} conversation notes",
    )

    t = time.perf_counter()
    persona = persona_snapshot(db, user)
    mark("persona", t, f"{persona.communication_style} · {persona.tone} · {persona.response_length}")

    t = time.perf_counter()
    context: AssembledContext = assemble_context(retrieval)
    mark("assemble", t, f"{len(context.items)} memories in context")

    t = time.perf_counter()
    system = build_system_prompt(persona, user_settings.creativity)
    messages = _clean_history(history, settings.SHORT_TERM_MEMORY_MESSAGES)
    messages.append({"role": "user", "content": build_user_turn(query, analysis, context)})
    mark("prompt", t, f"{len(messages) - 1} prior turns of short-term memory")

    t = time.perf_counter()
    ai = get_ai_service()
    try:
        generation = ai.generate(
            GenerationRequest(
                system=system,
                messages=messages,
                creativity=user_settings.creativity,
                persona=persona,
                analysis=analysis,
                context=context,
                query=query,
            )
        )
    except AIProviderError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    mark("generate", t, f"{generation.provider} · {generation.model}")

    t = time.perf_counter()
    try:
        validated = validate_response(generation.text, context)
    except EmptyResponseError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    detail = f"{len(validated.cited_labels)} citations verified"
    if validated.removed_labels:
        detail += f" · {len(validated.removed_labels)} invalid removed"
    if validated.unsupported_memory_claim:
        detail += " · unsupported memory claim flagged"
    mark("validate", t, detail)

    cited = set(validated.cited_labels)
    sources = [
        SourceRef(
            label=item.label,
            source_type=item.memory.source_type,
            source_id=item.memory.source_id,
            title=item.memory.title,
            snippet=item.memory.snippet,
            score=round(item.memory.score, 4),
            cited=item.label in cited,
        )
        for item in context.items
    ]
    latency = int((time.perf_counter() - started) * 1000)
    return PipelineResult(
        text=validated.text,
        grounding=validated.grounding,
        analysis=analysis,
        sources=sources,
        provider=generation.provider,
        model=generation.model,
        latency_ms=latency,
        trace={
            "steps": steps,
            "topic": analysis.topic,
            "intent": analysis.intent,
            "retrieval_ms": retrieval.timings_ms,
            "unsupported_memory_claim": validated.unsupported_memory_claim,
        },
        notice=" ".join(n for n in (retrieval_notice, generation.notice) if n) or None,
        degraded=generation.degraded or retrieval_notice is not None,
    )


def _title_from(text: str, limit: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def _apply_result(message: Message, result: PipelineResult) -> None:
    message.content = result.text
    message.topic = result.analysis.topic
    message.grounding = result.grounding
    message.provider = result.provider
    message.model = result.model
    message.latency_ms = result.latency_ms
    message.trace = {**result.trace, "notice": result.notice, "degraded": result.degraded}
    message.sources = [
        MessageSource(
            label=s.label,
            source_type=s.source_type,
            source_id=s.source_id,
            title=s.title[:200],
            snippet=s.snippet,
            score=s.score,
            cited=s.cited,
        )
        for s in result.sources
    ]


def get_owned_conversation(db: Session, user: User, conversation_id: int) -> Conversation:
    conv = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


def get_owned_message(db: Session, user: User, message_id: int) -> Message:
    msg = db.scalar(select(Message).where(Message.id == message_id, Message.user_id == user.id))
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return msg


MAX_MEMORY_CONTENT = 6000


def remember_exchange(db: Session, user: User, assistant: Message) -> ConversationMemory:
    """Store an exchange as an opt-in conversation memory (labelled as AI-assisted).

    Idempotent per message: remembering the same reply twice updates the existing
    memory instead of creating a duplicate (also used to resync after regenerate)."""
    question = db.scalar(
        select(Message)
        .where(
            Message.conversation_id == assistant.conversation_id,
            Message.user_id == user.id,
            Message.role == "user",
            Message.id < assistant.id,
        )
        .order_by(Message.id.desc())
        .limit(1)
    )
    flagged = bool((assistant.trace or {}).get("unsupported_memory_claim"))
    answer = re.sub(r"_Transparency note:.*?_", "", CITATION_RE.sub("", assistant.content), flags=re.S).strip()
    summary = " ".join(split_sentences(answer)[:4]) or answer[:600]
    q_text = question.content if question else "(question not available)"
    content = f"Question: {q_text}\nMentor's answer (summary): {summary}"
    if flagged:
        content += (
            "\nNote: this answer contained personal-sounding phrasing that is not backed by a recorded "
            "experience; treat it as general guidance."
        )

    mem = db.scalar(
        select(ConversationMemory).where(
            ConversationMemory.user_id == user.id, ConversationMemory.message_id == assistant.id
        )
    )
    if mem is None:
        mem = ConversationMemory(user_id=user.id, conversation_id=assistant.conversation_id, message_id=assistant.id)
        db.add(mem)
    mem.title = _title_from(q_text, 120)
    mem.content = content[:MAX_MEMORY_CONTENT]
    mem.topic = assistant.topic
    index_conversation_memory(mem)
    return mem


def remembered_message_ids(db: Session, user: User, message_ids: list[int]) -> set[int]:
    if not message_ids:
        return set()
    rows = db.scalars(
        select(ConversationMemory.message_id).where(
            ConversationMemory.user_id == user.id, ConversationMemory.message_id.in_(message_ids)
        )
    )
    return {int(r) for r in rows if r is not None}


def send_message(
    db: Session,
    user: User,
    text: str,
    conversation_id: int | None,
    ephemeral_history: list[HistoryTurn],
) -> ExchangeResult:
    user_settings = get_or_create_settings(db, user)
    settings = get_settings()

    if not user_settings.save_conversations:
        # Privacy mode: nothing about this exchange is written to the database.
        result = run_pipeline(db, user, text, ephemeral_history, user_settings)
        return ExchangeResult(None, None, None, result, persisted=False)

    conv = get_owned_conversation(db, user, conversation_id) if conversation_id else None
    if conv is None:
        conv = Conversation(user_id=user.id, title=_title_from(text))
        db.add(conv)
        db.flush()
        history: list[HistoryTurn] = []
    else:
        recent = db.scalars(
            select(Message)
            .where(Message.conversation_id == conv.id, Message.user_id == user.id)
            .order_by(Message.id.desc())
            .limit(settings.SHORT_TERM_MEMORY_MESSAGES)
        ).all()
        history = [HistoryTurn(m.role, m.content) for m in reversed(recent)]

    result = run_pipeline(db, user, text, history, user_settings, previous_topic=conv.topic)

    user_msg = Message(
        conversation_id=conv.id, user_id=user.id, role="user", content=text, topic=result.analysis.topic
    )
    assistant = Message(conversation_id=conv.id, user_id=user.id, role="assistant", content="")
    _apply_result(assistant, result)
    db.add_all([user_msg, assistant])
    conv.topic = result.analysis.topic if result.analysis.topic != "general" else conv.topic
    conv.updated_at = utcnow()
    db.flush()

    remembered_id = None
    if user_settings.auto_remember and result.analysis.intent != "smalltalk":
        memory = remember_exchange(db, user, assistant)
        db.flush()
        remembered_id = memory.id
    db.commit()
    db.refresh(assistant)
    return ExchangeResult(conv, user_msg, assistant, result, persisted=True, remembered_id=remembered_id)


def regenerate_message(db: Session, user: User, message_id: int) -> tuple[Message, PipelineResult]:
    assistant = get_owned_message(db, user, message_id)
    if assistant.role != "assistant":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only mentor replies can be regenerated")
    prior = db.scalars(
        select(Message)
        .where(Message.conversation_id == assistant.conversation_id, Message.user_id == user.id, Message.id < assistant.id)
        .order_by(Message.id)
    ).all()
    if not prior or prior[-1].role != "user":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No question found to regenerate from")
    question = prior[-1]
    history = [HistoryTurn(m.role, m.content) for m in prior[:-1]]
    user_settings = get_or_create_settings(db, user)
    result = run_pipeline(db, user, question.content, history, user_settings, previous_topic=question.topic)
    assistant.sources.clear()
    db.flush()
    _apply_result(assistant, result)
    assistant.feedback = None
    assistant.created_at = utcnow()
    db.flush()
    if remembered_message_ids(db, user, [assistant.id]):
        remember_exchange(db, user, assistant)  # keep the saved memory in sync with the new answer
    db.commit()
    db.refresh(assistant)
    return assistant, result

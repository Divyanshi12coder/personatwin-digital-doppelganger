"""Dashboard + analytics, computed from the user's real rows only.

Aggregation is done with simple column selects and Python grouping so the same
code works on PostgreSQL and SQLite. Every query is filtered by ``user_id``.
"""

from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Conversation,
    ConversationMemory,
    ExperienceMemory,
    KnowledgeChunk,
    KnowledgeDocument,
    Message,
    Tag,
    User,
    conversation_memory_tags,
    experience_tags,
    knowledge_document_tags,
)
from app.services.ai import get_ai_service
from app.services.profile import get_mentor, get_or_create_personality, profile_completeness
from app.services.query_understanding import TOPIC_LABELS


def _count(db: Session, stmt: Any) -> int:
    return int(db.scalar(stmt) or 0)


def _as_date(value: datetime) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).date()


def overview(db: Session, user: User) -> dict[str, Any]:
    uid = user.id
    docs = _count(db, select(func.count()).select_from(KnowledgeDocument).where(KnowledgeDocument.user_id == uid))
    chunks = _count(db, select(func.count()).select_from(KnowledgeChunk).where(KnowledgeChunk.user_id == uid))
    unindexed_chunks = _count(
        db,
        select(func.count()).select_from(KnowledgeChunk).where(KnowledgeChunk.user_id == uid, KnowledgeChunk.embedding.is_(None)),
    )
    exps = _count(db, select(func.count()).select_from(ExperienceMemory).where(ExperienceMemory.user_id == uid))
    unindexed_exps = _count(
        db,
        select(func.count())
        .select_from(ExperienceMemory)
        .where(ExperienceMemory.user_id == uid, ExperienceMemory.embedding.is_(None)),
    )
    exps_with_lessons = _count(
        db,
        select(func.count())
        .select_from(ExperienceMemory)
        .where(ExperienceMemory.user_id == uid, func.length(ExperienceMemory.lesson_learned) > 0),
    )
    conv_mems = _count(db, select(func.count()).select_from(ConversationMemory).where(ConversationMemory.user_id == uid))
    unindexed_conv = _count(
        db,
        select(func.count())
        .select_from(ConversationMemory)
        .where(ConversationMemory.user_id == uid, ConversationMemory.embedding.is_(None)),
    )
    conversations = _count(db, select(func.count()).select_from(Conversation).where(Conversation.user_id == uid))
    messages = _count(
        db, select(func.count()).select_from(Message).where(Message.user_id == uid, Message.role == "user")
    )
    categories = _count(
        db, select(func.count(func.distinct(KnowledgeDocument.category))).where(KnowledgeDocument.user_id == uid)
    )

    mentor = get_mentor(db, user)
    personality = get_or_create_personality(db, user)
    completeness, missing = profile_completeness(mentor, personality)

    total_vectors = chunks + exps + conv_mems
    unindexed = unindexed_chunks + unindexed_exps + unindexed_conv
    indexed_ratio = 1.0 if total_vectors == 0 else (total_vectors - unindexed) / total_vectors
    issues: list[str] = []
    if docs == 0:
        issues.append("Add knowledge so the mentor has notes to draw on.")
    if exps == 0:
        issues.append("Record a few experiences — they make advice genuinely personal.")
    elif exps_with_lessons < exps:
        issues.append(f"{exps - exps_with_lessons} experience(s) have no 'what I learned' yet.")
    if unindexed:
        issues.append(f"{unindexed} memory item(s) are not indexed — run a re-index from Settings.")
    if completeness < 70:
        issues.append("Fill in more of your mentoring philosophy for a more faithful voice.")
    if docs + exps == 0:
        health = "empty"
    elif unindexed or len(issues) > 2:
        health = "needs_attention"
    else:
        health = "healthy"

    since = datetime.now(timezone.utc) - timedelta(days=30)
    topic_rows = db.execute(
        select(Message.topic, func.count())
        .where(Message.user_id == uid, Message.role == "user", Message.created_at >= since)
        .group_by(Message.topic)
    ).all()
    active_topics = sorted(
        ({"topic": t, "label": TOPIC_LABELS.get(t, t.title()), "count": int(c)} for t, c in topic_rows),
        key=lambda r: r["count"],
        reverse=True,
    )[:6]

    recent = db.scalars(
        select(Conversation).where(Conversation.user_id == uid).order_by(Conversation.updated_at.desc()).limit(5)
    ).all()
    msg_counts: dict[int, int] = {}
    if recent:
        rows = db.execute(
            select(Message.conversation_id, func.count())
            .where(Message.user_id == uid, Message.conversation_id.in_([c.id for c in recent]))
            .group_by(Message.conversation_id)
        ).all()
        msg_counts = {int(cid): int(n) for cid, n in rows}

    ai = get_ai_service()
    return {
        "counts": {
            "knowledge_documents": docs,
            "knowledge_chunks": chunks,
            "experiences": exps,
            "conversation_memories": conv_mems,
            "total_memories": docs + exps + conv_mems,
            "conversations": conversations,
            "questions_asked": messages,
        },
        "profile": {
            "mentor_name": mentor.mentor_name if mentor else None,
            "bio": mentor.bio if mentor else "",
            "expertise_areas": mentor.expertise_areas if mentor else [],
            "mentoring_domains": mentor.mentoring_domains if mentor else [],
            "communication_style": personality.communication_style,
            "tone": personality.tone,
            "values": personality.values,
            "completeness": completeness,
            "missing": missing,
        },
        "memory_health": {
            "status": health,
            "indexed_ratio": round(indexed_ratio, 3),
            "unindexed_items": unindexed,
            "categories_covered": categories,
            "experiences_with_lessons": exps_with_lessons,
            "issues": issues,
        },
        "active_topics": active_topics,
        "recent_conversations": [
            {
                "id": c.id,
                "title": c.title,
                "topic": c.topic,
                "updated_at": c.updated_at,
                "message_count": msg_counts.get(c.id, 0),
            }
            for c in recent
        ],
        "ai": {"mode": ai.mode, "provider": ai.provider.name, "model": ai.provider.model},
    }


def analytics(db: Session, user: User, days: int = 90) -> dict[str, Any]:
    uid = user.id
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=days - 1)

    topic_counts = Counter(
        t for (t,) in db.execute(select(Message.topic).where(Message.user_id == uid, Message.role == "user"))
    )
    topics = [
        {"topic": t, "label": TOPIC_LABELS.get(t, t.title()), "count": c} for t, c in topic_counts.most_common()
    ]

    cat_counts = Counter(
        c for (c,) in db.execute(select(KnowledgeDocument.category).where(KnowledgeDocument.user_id == uid))
    )
    exp_counts = Counter(
        c for (c,) in db.execute(select(ExperienceMemory.experience_type).where(ExperienceMemory.user_id == uid))
    )

    # Messages per day (user questions vs mentor replies) within the window.
    per_day: dict[date, dict[str, int]] = {start + timedelta(days=i): {"questions": 0, "replies": 0} for i in range(days)}
    for role, created in db.execute(select(Message.role, Message.created_at).where(Message.user_id == uid)):
        d = _as_date(created)
        if d in per_day:
            per_day[d]["questions" if role == "user" else "replies"] += 1
    conversation_trend = [{"date": d.isoformat(), **v} for d, v in per_day.items()]

    # Mentoring sessions (conversations started) per ISO week.
    weeks: Counter[str] = Counter()
    for (created,) in db.execute(select(Conversation.created_at).where(Conversation.user_id == uid)):
        d = _as_date(created)
        monday = d - timedelta(days=d.weekday())
        weeks[monday.isoformat()] += 1
    sessions = [{"week": w, "sessions": weeks[w]} for w in sorted(weeks)]

    # Cumulative memory growth per day.
    events: list[tuple[date, str]] = []
    for (c,) in db.execute(select(KnowledgeDocument.created_at).where(KnowledgeDocument.user_id == uid)):
        events.append((_as_date(c), "knowledge"))
    for (c,) in db.execute(select(ExperienceMemory.created_at).where(ExperienceMemory.user_id == uid)):
        events.append((_as_date(c), "experiences"))
    for (c,) in db.execute(select(ConversationMemory.created_at).where(ConversationMemory.user_id == uid)):
        events.append((_as_date(c), "conversation"))
    events.sort()
    growth: list[dict[str, Any]] = []
    totals = {"knowledge": 0, "experiences": 0, "conversation": 0}
    for d, kind in events:
        totals[kind] += 1
        point = {"date": d.isoformat(), **totals}
        if growth and growth[-1]["date"] == point["date"]:
            growth[-1] = point
        else:
            growth.append(point)

    tag_usage: Counter[str] = Counter()
    for table, col in (
        (knowledge_document_tags, knowledge_document_tags.c.tag_id),
        (experience_tags, experience_tags.c.tag_id),
        (conversation_memory_tags, conversation_memory_tags.c.tag_id),
    ):
        rows = db.execute(
            select(Tag.name, func.count()).join(table, col == Tag.id).where(Tag.user_id == uid).group_by(Tag.name)
        )
        for name, count in rows:
            tag_usage[name] += int(count)

    feedback = Counter(
        f
        for (f,) in db.execute(
            select(Message.feedback).where(Message.user_id == uid, Message.role == "assistant", Message.feedback.is_not(None))
        )
    )
    grounding = Counter(
        g
        for (g,) in db.execute(
            select(Message.grounding).where(Message.user_id == uid, Message.role == "assistant", Message.grounding.is_not(None))
        )
    )

    return {
        "window_days": days,
        "topics": topics,
        "knowledge_categories": [{"category": k, "count": v} for k, v in cat_counts.most_common()],
        "experience_types": [{"type": k, "count": v} for k, v in exp_counts.most_common()],
        "conversation_trend": conversation_trend,
        "sessions_by_week": sessions,
        "memory_growth": growth,
        "top_tags": [{"tag": k, "count": v} for k, v in tag_usage.most_common(12)],
        "feedback": {"up": feedback.get("up", 0), "down": feedback.get("down", 0)},
        "grounding": {k: grounding.get(k, 0) for k in ("grounded", "partial", "ungrounded")},
    }

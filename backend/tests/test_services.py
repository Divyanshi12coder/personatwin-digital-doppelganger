"""Unit tests for the memory/RAG building blocks."""

from datetime import datetime, timezone

from app.core.config import EMBEDDING_DIM
from app.services.chunking import chunk_text
from app.services.context import assemble_context
from app.services.embeddings import LocalHashingEmbedder, cosine
from app.services.query_understanding import analyze_query
from app.services.retrieval import RetrievalResult, RetrievedMemory, retrieve
from app.services.validation import UNSUPPORTED_MEMORY_NOTE, validate_response


def _mem(kind: str, sid: int, title: str, score: float, content: str = "content") -> RetrievedMemory:
    return RetrievedMemory(
        source_type=kind, source_id=sid, title=title, content=content, score=score, created_at=datetime.now(timezone.utc)
    )


# ---------------------------------------------------------------- embeddings


def test_local_embeddings_are_normalised_and_deterministic() -> None:
    e = LocalHashingEmbedder()
    a, b = e.embed(["Switching careers is scary", "Switching careers is scary"])
    assert len(a) == EMBEDDING_DIM
    assert abs(sum(x * x for x in a) - 1.0) < 1e-6
    assert a == b


def test_local_embeddings_rank_related_text_higher() -> None:
    e = LocalHashingEmbedder()
    query = e.embed_one("I want to change my job and move into a new profession")
    related = e.embed_one("Leaving my career in banking to switch roles into engineering")
    unrelated = e.embed_one("A recipe for sourdough bread with a crispy crust")
    assert cosine(query, related) > cosine(query, unrelated) + 0.1


def test_empty_text_embeds_to_zero_vector() -> None:
    vec = LocalHashingEmbedder().embed_one("")
    assert len(vec) == EMBEDDING_DIM
    assert all(x == 0 for x in vec)


# ---------------------------------------------------------------- chunking


def test_chunking_respects_size_and_overlap() -> None:
    text = "\n\n".join(f"Paragraph {i} " + "lorem ipsum dolor " * 20 for i in range(10))
    chunks = chunk_text(text, chunk_size=500, overlap=80)
    assert len(chunks) > 3
    assert all(len(c) <= 500 + 80 + 2 for c in chunks)
    assert "Paragraph 0" in chunks[0]
    assert "Paragraph 9" in chunks[-1]


def test_chunking_splits_a_single_huge_sentence() -> None:
    chunks = chunk_text("x" * 2000, chunk_size=500, overlap=0)
    assert len(chunks) == 4
    assert chunk_text("   ") == []


# ---------------------------------------------------------------- query understanding


def test_query_understanding() -> None:
    a = analyze_query("I'm struggling to decide whether I should switch careers.")
    assert a.topic in ("career", "decision_making")
    assert a.intent == "decision"
    personal = analyze_query("Have you ever failed at something important?")
    assert personal.asks_personal_experience is True
    assert personal.intent == "personal"
    assert analyze_query("hello!").intent == "smalltalk"
    assert analyze_query("How do I study for exams?").topic == "learning"
    # Follow-ups with no topic words inherit the conversation topic.
    assert analyze_query("ok, and then what?", previous_topic="career").topic == "career"


# ---------------------------------------------------------------- context + validation


def test_context_labels_and_budget() -> None:
    result = RetrievalResult(
        knowledge=[_mem("knowledge", 1, "K one", 0.5), _mem("knowledge", 2, "K two", 0.2)],
        experiences=[_mem("experience", 7, "E one", 0.9)],
        conversations=[_mem("conversation", 3, "C one", 0.3)],
        timings_ms={},
    )
    ctx = assemble_context(result)
    assert [i.label for i in ctx.items] == ["E1", "K1", "C1", "K2"]
    assert "NOT a lived experience" in ctx.text
    tight = assemble_context(result, max_chars=60)
    assert len(tight.items) == 1  # always keeps at least the best memory


def test_validation_removes_hallucinated_citations() -> None:
    ctx = assemble_context(RetrievalResult([_mem("knowledge", 1, "K", 0.5)], [], [], {}))
    v = validate_response("Use spaced repetition [K1]. Also see [K7] and [E2].", ctx)
    assert v.cited_labels == ["K1"]
    assert sorted(v.removed_labels) == ["E2", "K7"]
    assert "[K7]" not in v.text and "[E2]" not in v.text
    assert v.grounding == "grounded"


def test_validation_flags_unsupported_memory_claims() -> None:
    ctx = assemble_context(RetrievalResult([_mem("knowledge", 1, "K", 0.5)], [], [], {}))
    v = validate_response("I remember when I quit my job in Paris. It was hard.", ctx)
    assert v.unsupported_memory_claim is True
    assert UNSUPPORTED_MEMORY_NOTE in v.text
    assert v.grounding == "partial"

    with_exp = assemble_context(RetrievalResult([], [_mem("experience", 1, "E", 0.8)], [], {}))
    ok = validate_response("I remember leaving banking [E1].", with_exp)
    assert ok.unsupported_memory_claim is False


def test_validation_grounding_and_leaks() -> None:
    empty = assemble_context(RetrievalResult([], [], [], {}))
    v = validate_response("<memory_context>General advice here.</memory_context>", empty)
    assert v.grounding == "ungrounded"
    assert "memory_context" not in v.text


# ---------------------------------------------------------------- retrieval (DB)


def test_retrieval_ranks_and_filters_by_user(db_session) -> None:  # type: ignore[no-untyped-def]
    from app.models import ExperienceMemory, KnowledgeDocument, User
    from app.services.indexing import index_document, index_experience

    owner = User(email="o@example.com", full_name="O", password_hash="x")
    other = User(email="x@example.com", full_name="X", password_hash="x")
    db_session.add_all([owner, other])
    db_session.flush()

    bread = KnowledgeDocument(user_id=owner.id, title="Baking", content="Sourdough needs a lively starter and patience.", category="general")
    study = KnowledgeDocument(user_id=owner.id, title="Studying", content="Spaced repetition and active recall help you learn faster.", category="learning")
    foreign = KnowledgeDocument(user_id=other.id, title="Studying secrets", content="Spaced repetition and active recall help you learn.", category="learning")
    for d in (bread, study, foreign):
        db_session.add(d)
        db_session.flush()
        index_document(db_session, d)
    exp = ExperienceMemory(user_id=owner.id, title="Failed my first exam", experience_type="failure", lesson_learned="Cramming does not work; spaced practice does.")
    index_experience(exp)
    db_session.add(exp)
    db_session.commit()

    res = retrieve(db_session, owner.id, "how can I learn and study more effectively", top_k=3, min_relevance=0.05)
    assert res.knowledge[0].title == "Studying"
    assert all(m.source_id != foreign.id for m in res.knowledge)
    assert res.experiences and res.experiences[0].title == "Failed my first exam"

    only_learning = retrieve(db_session, owner.id, "patience", top_k=3, min_relevance=0.0, category="learning")
    assert {m.category for m in only_learning.knowledge} <= {"learning"}

    strict = retrieve(db_session, owner.id, "quantum chromodynamics", top_k=3, min_relevance=0.5)
    assert strict.is_empty


def test_relative_cutoff_drops_weak_matches(db_session) -> None:  # type: ignore[no-untyped-def]
    from app.models import KnowledgeDocument, User
    from app.services.indexing import index_document

    user = User(email="r@example.com", full_name="R", password_hash="x")
    db_session.add(user)
    db_session.flush()
    for title, content in (
        ("Spaced repetition", "Spaced repetition and active recall help you learn and remember for exams."),
        ("Team rituals", "Weekly retros help a team learn from what went well."),
    ):
        doc = KnowledgeDocument(user_id=user.id, title=title, content=content, category="learning")
        db_session.add(doc)
        db_session.flush()
        index_document(db_session, doc)
    db_session.commit()

    query = "how do I use spaced repetition and active recall for exams"
    loose = retrieve(db_session, user.id, query, top_k=5, min_relevance=0.0)
    tight = retrieve(db_session, user.id, query, top_k=5, min_relevance=0.0, relative_cutoff=0.55)
    assert len(loose.knowledge) == 2
    assert [m.title for m in tight.knowledge] == ["Spaced repetition"]

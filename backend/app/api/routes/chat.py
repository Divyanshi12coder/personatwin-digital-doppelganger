"""Mentor chat + conversation history."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser, chat_rate_limit
from app.db.base import utcnow
from app.models import Conversation, Message
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationOut,
    ConversationUpdate,
    FeedbackRequest,
    MessageOut,
    SourceOut,
)
from app.services.chat import (
    HistoryTurn,
    PipelineResult,
    get_owned_conversation,
    get_owned_message,
    regenerate_message,
    remember_exchange,
    remembered_message_ids,
    send_message,
)

router = APIRouter(tags=["chat"])


def message_out(m: Message, remembered: bool = False) -> MessageOut:
    trace = m.trace or None
    return MessageOut(
        id=m.id,
        role=m.role,
        content=m.content,
        created_at=m.created_at,
        topic=m.topic,
        feedback=m.feedback,
        grounding=m.grounding,
        provider=m.provider,
        model=m.model,
        latency_ms=m.latency_ms,
        sources=[SourceOut.model_validate(s) for s in m.sources],
        trace=trace,
        remembered=remembered,
    )


def _ephemeral_out(role: str, content: str, result: PipelineResult | None = None) -> MessageOut:
    if result is None:
        return MessageOut(id=None, role=role, content=content, created_at=utcnow())
    return MessageOut(
        id=None,
        role=role,
        content=result.text,
        created_at=utcnow(),
        topic=result.analysis.topic,
        grounding=result.grounding,
        provider=result.provider,
        model=result.model,
        latency_ms=result.latency_ms,
        sources=[SourceOut.model_validate(s, from_attributes=True) for s in result.sources],
        trace={**result.trace, "notice": result.notice, "degraded": result.degraded},
    )


# ----------------------------------------------------------------- chat


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(chat_rate_limit)])
def chat(body: ChatRequest, user: CurrentUser, db: DB) -> ChatResponse:
    history = [HistoryTurn(h.role, h.content) for h in body.history]
    outcome = send_message(db, user, body.message, body.conversation_id, history)
    if not outcome.persisted:
        return ChatResponse(
            conversation_id=None,
            conversation_title=None,
            persisted=False,
            user_message=_ephemeral_out("user", body.message),
            assistant_message=_ephemeral_out("assistant", "", outcome.pipeline),
        )
    assert outcome.conversation and outcome.user_message and outcome.assistant_message
    return ChatResponse(
        conversation_id=outcome.conversation.id,
        conversation_title=outcome.conversation.title,
        persisted=True,
        user_message=message_out(outcome.user_message),
        assistant_message=message_out(outcome.assistant_message, remembered=outcome.remembered_id is not None),
        remembered_memory_id=outcome.remembered_id,
    )


@router.post(
    "/chat/messages/{message_id}/regenerate", response_model=MessageOut, dependencies=[Depends(chat_rate_limit)]
)
def regenerate(message_id: int, user: CurrentUser, db: DB) -> MessageOut:
    message, _ = regenerate_message(db, user, message_id)
    return message_out(message, remembered=bool(remembered_message_ids(db, user, [message.id])))


@router.patch("/chat/messages/{message_id}/feedback", response_model=MessageOut)
def feedback(message_id: int, body: FeedbackRequest, user: CurrentUser, db: DB) -> MessageOut:
    message = get_owned_message(db, user, message_id)
    if message.role != "assistant":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback applies to mentor replies only")
    message.feedback = body.feedback
    db.commit()
    db.refresh(message)
    return message_out(message, remembered=bool(remembered_message_ids(db, user, [message.id])))


@router.post("/chat/messages/{message_id}/remember", status_code=status.HTTP_201_CREATED)
def remember(message_id: int, user: CurrentUser, db: DB) -> dict[str, int]:
    message = get_owned_message(db, user, message_id)
    if message.role != "assistant":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only mentor replies can be remembered")
    memory = remember_exchange(db, user, message)
    db.commit()
    return {"memory_id": memory.id}


# ----------------------------------------------------------------- conversations


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(user: CurrentUser, db: DB) -> list[ConversationOut]:
    convs = db.scalars(
        select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc()).limit(100)
    ).all()
    ids = [c.id for c in convs]
    counts: dict[int, int] = {}
    last: dict[int, str] = {}
    if ids:
        counts = {
            int(cid): int(n)
            for cid, n in db.execute(
                select(Message.conversation_id, func.count())
                .where(Message.user_id == user.id, Message.conversation_id.in_(ids))
                .group_by(Message.conversation_id)
            )
        }
        last_ids = select(func.max(Message.id)).where(Message.user_id == user.id, Message.conversation_id.in_(ids)).group_by(
            Message.conversation_id
        )
        for m in db.scalars(select(Message).where(Message.id.in_(last_ids))):
            last[m.conversation_id] = " ".join(m.content.split())[:140]
    return [
        ConversationOut(
            id=c.id,
            title=c.title,
            topic=c.topic,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=counts.get(c.id, 0),
            last_message=last.get(c.id),
        )
        for c in convs
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: int, user: CurrentUser, db: DB) -> ConversationDetail:
    conv = get_owned_conversation(db, user, conversation_id)
    remembered = remembered_message_ids(db, user, [m.id for m in conv.messages])
    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        topic=conv.topic,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(conv.messages),
        messages=[message_out(m, remembered=m.id in remembered) for m in conv.messages],
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
def rename_conversation(conversation_id: int, body: ConversationUpdate, user: CurrentUser, db: DB) -> ConversationOut:
    conv = get_owned_conversation(db, user, conversation_id)
    conv.title = " ".join(body.title.split())
    db.commit()
    return ConversationOut(
        id=conv.id, title=conv.title, topic=conv.topic, created_at=conv.created_at, updated_at=conv.updated_at
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: int, user: CurrentUser, db: DB) -> Response:
    db.delete(get_owned_conversation(db, user, conversation_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

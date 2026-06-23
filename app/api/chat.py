from __future__ import annotations

from fastapi import APIRouter, status

from app.schemas.chat import (
    CreateSessionRequest,
    CreateSessionResponse,
    DeleteSessionResponse,
    ListSessionsResponse,
    MessageItem,
    NewsCardItem,
    SendMessageRequest,
    SendMessageResponse,
    SessionDetailResponse,
    SessionSummary,
    UpdateSessionRequest,
    UpdateSessionResponse,
)
from app.services.chat import (
    create_session,
    delete_session,
    get_session_with_messages,
    list_sessions,
    send_message,
    update_session,
)

router = APIRouter(prefix="/chat", tags=["chat"])


# ─────────────────────────────────────────────
# Session
# ─────────────────────────────────────────────

@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_chat_session(request: CreateSessionRequest) -> CreateSessionResponse:
    data = create_session(title=request.title)
    return CreateSessionResponse(
        session_id=data["id"],
        title=data.get("title"),
        created_at=data["created_at"],
    )


@router.get("/sessions")
async def list_chat_sessions() -> ListSessionsResponse:
    sessions = list_sessions()
    return ListSessionsResponse(
        sessions=[
            SessionSummary(
                session_id=s["id"],
                title=s.get("title"),
                updated_at=s["updated_at"],
            )
            for s in sessions
        ]
    )


@router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str) -> SessionDetailResponse:
    data = get_session_with_messages(session_id)
    return SessionDetailResponse(
        session_id=data["id"],
        title=data.get("title"),
        created_at=data["created_at"],
        messages=[_to_message_item(m) for m in data["messages"]],
    )


@router.patch("/sessions/{session_id}")
async def update_chat_session(
    session_id: str, request: UpdateSessionRequest
) -> UpdateSessionResponse:
    data = update_session(session_id, title=request.title)
    return UpdateSessionResponse(session_id=data["id"], title=data.get("title"))


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str) -> DeleteSessionResponse:
    delete_session(session_id)
    return DeleteSessionResponse(deleted=True)


# ─────────────────────────────────────────────
# Message
# ─────────────────────────────────────────────

@router.post("/sessions/{session_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    session_id: str, request: SendMessageRequest
) -> SendMessageResponse:
    result = send_message(session_id=session_id, user_message=request.message)
    msg = result["message"]
    cards = result["news_cards"]

    return SendMessageResponse(
        message=_to_message_item(msg),
        news_cards=[_to_card_item(c) for c in cards],
    )


# ─────────────────────────────────────────────
# 변환 헬퍼
# ─────────────────────────────────────────────

def _to_message_item(msg: dict) -> MessageItem:
    return MessageItem(
        message_id=msg["id"],
        role=msg["role"],
        content=msg["content"],
        intent=msg.get("intent"),
        verdict=msg.get("verdict"),
        news_cards=[_to_card_item(c) for c in msg.get("news_cards", [])],
        created_at=msg.get("created_at"),
    )


def _to_card_item(card: dict) -> NewsCardItem:
    return NewsCardItem(
        card_id=card["id"],
        title=card["title"],
        summary=card.get("summary"),
        url=card["url"],
        source=card["source"],
        published_at=card.get("published_at"),
    )
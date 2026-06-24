from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


# 공통 서브 모델

class NewsCardItem(BaseModel):
    card_id: str
    title: str
    summary: str | None = None
    url: str
    source: Literal["internal", "web"]
    published_at: datetime | None = None


class MessageItem(BaseModel):
    message_id: str
    role: Literal["user", "assistant"]
    content: str
    intent: Literal["explore", "factcheck"] | None = None
    verdict: Literal["true", "false", "unclear"] | None = None
    news_cards: list[NewsCardItem] = []
    created_at: datetime | None = None


# Session API

class CreateSessionRequest(BaseModel):
    title: str | None = None


class CreateSessionResponse(BaseModel):
    session_id: str
    title: str | None = None
    created_at: datetime


class SessionSummary(BaseModel):
    session_id: str
    title: str | None = None
    updated_at: datetime


class ListSessionsResponse(BaseModel):
    sessions: list[SessionSummary]


class SessionDetailResponse(BaseModel):
    session_id: str
    title: str | None = None
    created_at: datetime
    messages: list[MessageItem]


class UpdateSessionRequest(BaseModel):
    title: str


class UpdateSessionResponse(BaseModel):
    session_id: str
    title: str | None = None


class DeleteSessionResponse(BaseModel):
    deleted: bool


# Message API

class SendMessageRequest(BaseModel):
    message: str


class SendMessageResponse(BaseModel):
    message: MessageItem
    news_cards: list[NewsCardItem] = []
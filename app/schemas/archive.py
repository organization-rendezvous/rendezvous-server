from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


# ─────────────────────────────────────────────
# 공통 서브 모델
# ─────────────────────────────────────────────

class StyleItem(BaseModel):
    style_id: str
    start_offset: int
    end_offset: int
    style_type: Literal["bold", "underline", "highlight", "color"]
    style_value: str | None = None  # highlight/color일 때 색상값 (예: "yellow")


class CommentItem(BaseModel):
    comment_id: str
    start_offset: int
    end_offset: int
    content: str
    created_at: datetime
    updated_at: datetime


class ArchiveListItem(BaseModel):
    archive_id: str
    topic: str
    title: str
    summary: str
    keywords: list[str]
    saved_at: datetime


# ─────────────────────────────────────────────
# 보관 (Archive)
# ─────────────────────────────────────────────

class CreateArchiveRequest(BaseModel):
    trend_id: str


class CreateArchiveResponse(BaseModel):
    archive_id: str
    saved_at: datetime


class DeleteArchiveResponse(BaseModel):
    deleted: bool


# ─────────────────────────────────────────────
# 보관 여부 확인
# ─────────────────────────────────────────────

class CheckArchiveResponse(BaseModel):
    is_archived: bool
    archive_id: str | None = None


# ─────────────────────────────────────────────
# 보관함 목록
# ─────────────────────────────────────────────

class ListArchiveResponse(BaseModel):
    items: list[ArchiveListItem]
    page: int
    size: int
    total: int


# ─────────────────────────────────────────────
# 보관 뉴스 상세
# ─────────────────────────────────────────────

class ArchiveDetailResponse(BaseModel):
    archive_id: str
    topic: str
    title: str
    summary: str
    detail_summary: str | None = None
    ai_comment: str | None = None
    keywords: list[str]
    links: list[dict]
    memo: str = ""
    styles: list[StyleItem]
    comments: list[CommentItem]
    saved_at: datetime


# ─────────────────────────────────────────────
# 내용 수정 (summary / detail_summary / ai_comment)
# ─────────────────────────────────────────────

class UpdateContentRequest(BaseModel):
    summary: str | None = None
    detail_summary: str | None = None
    ai_comment: str | None = None


class UpdateContentResponse(BaseModel):
    archive_id: str
    summary: str | None = None
    detail_summary: str | None = None
    ai_comment: str | None = None
    updated_at: datetime


# ─────────────────────────────────────────────
# 메모
# ─────────────────────────────────────────────

class UpdateMemoRequest(BaseModel):
    memo: str


class UpdateMemoResponse(BaseModel):
    archive_id: str
    memo: str


# ─────────────────────────────────────────────
# 스타일
# ─────────────────────────────────────────────

class CreateStyleRequest(BaseModel):
    start_offset: int
    end_offset: int
    style_type: Literal["bold", "underline", "highlight", "color"]
    style_value: str | None = None


class CreateStyleResponse(BaseModel):
    style_id: str
    start_offset: int
    end_offset: int
    style_type: str
    style_value: str | None = None


class DeleteStyleResponse(BaseModel):
    deleted: bool


# ─────────────────────────────────────────────
# 주석 (Comment)
# ─────────────────────────────────────────────

class CreateCommentRequest(BaseModel):
    start_offset: int
    end_offset: int
    content: str


class CreateCommentResponse(BaseModel):
    comment_id: str
    start_offset: int
    end_offset: int
    content: str
    created_at: datetime


class UpdateCommentRequest(BaseModel):
    content: str


class UpdateCommentResponse(BaseModel):
    comment_id: str
    content: str
    updated_at: datetime


class DeleteCommentResponse(BaseModel):
    deleted: bool
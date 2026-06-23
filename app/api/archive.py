from __future__ import annotations

from fastapi import APIRouter, status

from app.db.repository_factory import repository
from app.schemas.archive import (
    ArchiveDetailResponse,
    CheckArchiveResponse,
    CommentItem,
    CreateArchiveRequest,
    CreateArchiveResponse,
    CreateCommentRequest,
    CreateCommentResponse,
    CreateStyleRequest,
    CreateStyleResponse,
    DeleteArchiveResponse,
    DeleteCommentResponse,
    DeleteStyleResponse,
    ListArchiveResponse,
    ArchiveListItem,
    StyleItem,
    UpdateCommentRequest,
    UpdateCommentResponse,
    UpdateMemoRequest,
    UpdateMemoResponse,
)

router = APIRouter(prefix="/archive", tags=["archive"])


# ─────────────────────────────────────────────
# 보관 / 해제
# ─────────────────────────────────────────────

@router.post("/news", status_code=status.HTTP_201_CREATED)
async def create_archive(request: CreateArchiveRequest) -> CreateArchiveResponse:
    """뉴스 상세 데이터를 스냅샷으로 복제하여 보관함에 저장합니다."""
    # 원본 트렌드 상세 조회
    data = repository.get_trend_detail(request.trend_id)
    trend = data["trend"]
    topic = data["topic"]
    scores = data["scores"]
    links = data["links"]
    rank_history = data["rank_history"]

    # 점수 상세 직렬화
    score_detail = {k: v for k, v in scores.items() if k not in {"id", "trend_id", "created_at", "updated_at"}}

    # 링크 스냅샷 직렬화
    link_snapshot = [
        {
            "title": lk.get("title", ""),
            "url": lk.get("url", ""),
            "source_name": lk.get("source_name"),
            "source_type": lk.get("source_type", "news"),
            "summary": lk.get("summary"),
            "relevance_score": lk.get("relevance_score"),
        }
        for lk in links
    ]

    archive = repository.create_archive_news(
        trend_id=request.trend_id,
        topic=topic["topic_name"],
        title=trend["title"],
        summary=trend.get("summary", ""),
        detail_summary=trend.get("detail_summary"),
        ai_comment=trend.get("ai_comment"),
        keywords=trend.get("keywords", []),
        score_detail=score_detail,
        rank_graph=rank_history,
        links=link_snapshot,
    )

    return CreateArchiveResponse(
        archive_id=archive["id"],
        saved_at=archive["saved_at"],
    )


@router.delete("/news/{archive_id}")
async def delete_archive(archive_id: str) -> DeleteArchiveResponse:
    """보관 해제 — archive_news 및 연관 스타일/주석 cascade 삭제."""
    repository.delete_archive_news(archive_id)
    return DeleteArchiveResponse(deleted=True)


# ─────────────────────────────────────────────
# 보관 여부 확인
# ─────────────────────────────────────────────

@router.get("/news/check")
async def check_archive(title: str) -> CheckArchiveResponse:
    """제목 기준으로 현재 보관 여부를 확인합니다."""
    row = repository.check_archive_by_title(title=title)
    if row:
        return CheckArchiveResponse(is_archived=True, archive_id=row["id"])
    return CheckArchiveResponse(is_archived=False)


# ─────────────────────────────────────────────
# 보관함 목록
# ─────────────────────────────────────────────

@router.get("/news")
async def list_archive(
    topic: str | None = None,
    page: int = 1,
    size: int = 9,
) -> ListArchiveResponse:
    """보관된 뉴스 목록을 페이지네이션으로 조회합니다."""
    result = repository.list_archive_news(topic=topic, page=page, size=size)
    return ListArchiveResponse(
        items=[
            ArchiveListItem(
                archive_id=item["id"],
                topic=item["topic"],
                title=item["title"],
                summary=item["summary"],
                keywords=item.get("keywords", []),
                saved_at=item["saved_at"],
            )
            for item in result["items"]
        ],
        page=result["page"],
        size=result["size"],
        total=result["total"],
    )


# ─────────────────────────────────────────────
# 보관 뉴스 상세
# ─────────────────────────────────────────────

@router.get("/news/{archive_id}")
async def get_archive_detail(archive_id: str) -> ArchiveDetailResponse:
    """보관 뉴스 본문 + 스타일 + 주석을 함께 반환합니다."""
    news = repository.get_archive_news(archive_id)
    styles = repository.list_styles(archive_id)
    comments = repository.list_comments(archive_id)

    return ArchiveDetailResponse(
        archive_id=news["id"],
        topic=news["topic"],
        title=news["title"],
        summary=news["summary"],
        detail_summary=news.get("detail_summary"),
        ai_comment=news.get("ai_comment"),
        keywords=news.get("keywords", []),
        links=news.get("links", []),
        memo=news.get("memo", ""),
        styles=[
            StyleItem(
                style_id=s["id"],
                start_offset=s["start_offset"],
                end_offset=s["end_offset"],
                style_type=s["style_type"],
                style_value=s.get("style_value"),
            )
            for s in styles
        ],
        comments=[
            CommentItem(
                comment_id=c["id"],
                start_offset=c["start_offset"],
                end_offset=c["end_offset"],
                content=c["content"],
                created_at=c["created_at"],
                updated_at=c["updated_at"],
            )
            for c in comments
        ],
        saved_at=news["saved_at"],
    )


# ─────────────────────────────────────────────
# 메모
# ─────────────────────────────────────────────

@router.patch("/news/{archive_id}/memo")
async def update_memo(archive_id: str, request: UpdateMemoRequest) -> UpdateMemoResponse:
    """뉴스 전체 메모를 수정합니다 (뉴스 1건당 1개)."""
    updated = repository.update_archive_memo(archive_id, memo=request.memo)
    return UpdateMemoResponse(archive_id=updated["id"], memo=updated["memo"])


# ─────────────────────────────────────────────
# 스타일 (서식)
# ─────────────────────────────────────────────

@router.post("/news/{archive_id}/styles", status_code=status.HTTP_201_CREATED)
async def create_style(archive_id: str, request: CreateStyleRequest) -> CreateStyleResponse:
    """선택한 텍스트 구간에 bold / underline / highlight / color 서식을 저장합니다."""
    saved = repository.save_style(
        archive_id=archive_id,
        start_offset=request.start_offset,
        end_offset=request.end_offset,
        style_type=request.style_type,
        style_value=request.style_value,
    )
    return CreateStyleResponse(
        style_id=saved["id"],
        start_offset=saved["start_offset"],
        end_offset=saved["end_offset"],
        style_type=saved["style_type"],
        style_value=saved.get("style_value"),
    )


@router.delete("/news/{archive_id}/styles/{style_id}")
async def delete_style(archive_id: str, style_id: str) -> DeleteStyleResponse:
    repository.delete_style(style_id)
    return DeleteStyleResponse(deleted=True)


# ─────────────────────────────────────────────
# 주석 (Comment)
# ─────────────────────────────────────────────

@router.post("/news/{archive_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(archive_id: str, request: CreateCommentRequest) -> CreateCommentResponse:
    """텍스트 구간을 드래그하여 주석을 추가합니다."""
    saved = repository.save_comment(
        archive_id=archive_id,
        start_offset=request.start_offset,
        end_offset=request.end_offset,
        content=request.content,
    )
    return CreateCommentResponse(
        comment_id=saved["id"],
        start_offset=saved["start_offset"],
        end_offset=saved["end_offset"],
        content=saved["content"],
        created_at=saved["created_at"],
    )


@router.patch("/news/{archive_id}/comments/{comment_id}")
async def update_comment(archive_id: str, comment_id: str, request: UpdateCommentRequest) -> UpdateCommentResponse:
    updated = repository.update_comment(comment_id, content=request.content)
    return UpdateCommentResponse(
        comment_id=updated["id"],
        content=updated["content"],
        updated_at=updated["updated_at"],
    )


@router.delete("/news/{archive_id}/comments/{comment_id}")
async def delete_comment(archive_id: str, comment_id: str) -> DeleteCommentResponse:
    repository.delete_comment(comment_id)
    return DeleteCommentResponse(deleted=True)
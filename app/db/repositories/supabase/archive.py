from __future__ import annotations

from app.core.errors import NotFoundError
from .base import utc_now


class ArchiveMixin:
    """archive_news / archive_news_links / archive_news_styles / archive_news_comments 관련 메서드."""

    # Archive News (보관 뉴스)
    def create_archive_news(
        self,
        *,
        user_id: str = "personal-user",
        trend_id: str,
        topic: str,
        title: str,
        summary: str,
        detail_summary: str | None = None,
        ai_comment: str | None = None,
        keywords: list[str] | None = None,
        score_detail: dict | None = None,
        rank_graph: list[dict] | None = None,
        links: list[dict] | None = None,
    ) -> dict:
        row = {
            "user_id": user_id,
            "trend_id": trend_id,
            "topic": topic,
            "title": title,
            "summary": summary,
            "detail_summary": detail_summary,
            "ai_comment": ai_comment,
            "keywords": keywords or [],
            "score_detail": score_detail or {},
            "rank_graph": rank_graph or [],
            "links": links or [],
            "saved_at": utc_now().isoformat(),
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
        }
        res = self.client.table("archive_news").insert(row).execute()
        return res.data[0]


    def get_archive_news(self, archive_id: str) -> dict:
        res = (
            self.client.table("archive_news")
            .select("*")
            .eq("id", archive_id)
            .single()
            .execute()
        )
        if not res.data:
            raise NotFoundError("보관 뉴스를 찾을 수 없습니다.")
        return res.data

    def list_archive_news(
        self,
        *,
        user_id: str = "personal-user",
        topic: str | None = None,
        page: int = 1,
        size: int = 9,
    ) -> dict:
        query = (
            self.client.table("archive_news")
            .select("id, topic, title, summary, keywords, saved_at", count="exact")
            .eq("user_id", user_id)
            .order("saved_at", desc=True)
        )
        if topic:
            query = query.eq("topic", topic)

        offset = (page - 1) * size
        query = query.range(offset, offset + size - 1)

        res = query.execute()
        return {
            "items": res.data or [],
            "total": res.count or 0,
            "page": page,
            "size": size,
        }


    def delete_archive_news(self, archive_id: str, *, user_id: str = "personal-user") -> bool:
        self.client.table("archive_news").delete().eq("id", archive_id).eq("user_id", user_id).execute()
        return True

    def check_archive_by_title(
        self,
        *,
        user_id: str = "personal-user",
        title: str,
    ) -> dict | None:
        res = (
            self.client.table("archive_news")
            .select("id")
            .eq("user_id", user_id)
            .eq("title", title)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None


    def update_archive_content(
        self,
        archive_id: str,
        *,
        title: str | None = None,
        summary: str | None = None,
        detail_summary: str | None = None,
        ai_comment: str | None = None,
        keywords: list[str] | None = None,
    ) -> dict:
        """title / summary / detail_summary / ai_comment / keywords partial update.
        포함된 필드만 업데이트되며, 원본 트렌드 데이터에는 영향 없습니다."""
        patch: dict = {"updated_at": utc_now().isoformat()}
        if title is not None:
            patch["title"] = title
        if summary is not None:
            patch["summary"] = summary
        if detail_summary is not None:
            patch["detail_summary"] = detail_summary
        if ai_comment is not None:
            patch["ai_comment"] = ai_comment
        if keywords is not None:
            patch["keywords"] = keywords

        res = (
            self.client.table("archive_news")
            .update(patch)
            .eq("id", archive_id)
            .execute()
        )
        if not res.data:
            raise NotFoundError("보관 뉴스를 찾을 수 없습니다.")
        return res.data[0]


    def update_archive_memo(self, archive_id: str, *, memo: str) -> dict:
        res = (
            self.client.table("archive_news")
            .update({"memo": memo, "updated_at": utc_now().isoformat()})
            .eq("id", archive_id)
            .execute()
        )
        if not res.data:
            raise NotFoundError("보관 뉴스를 찾을 수 없습니다.")
        return res.data[0]


    # Styles (텍스트 서식)
    def save_style(
        self,
        *,
        archive_id: str,
        start_offset: int,
        end_offset: int,
        style_type: str,
        style_value: str | None = None,
    ) -> dict:
        row = {
            "archive_news_id": archive_id,
            "start_offset": start_offset,
            "end_offset": end_offset,
            "style_type": style_type,
            "style_value": style_value,
            "created_at": utc_now().isoformat(),
        }
        res = self.client.table("archive_news_styles").insert(row).execute()
        return res.data[0]


    def list_styles(self, archive_id: str) -> list[dict]:
        res = (
            self.client.table("archive_news_styles")
            .select("*")
            .eq("archive_news_id", archive_id)
            .order("start_offset")
            .execute()
        )
        return res.data or []

    def delete_style(self, style_id: str) -> bool:
        self.client.table("archive_news_styles").delete().eq("id", style_id).execute()
        return True


    # Comments (주석)
    def save_comment(
        self,
        *,
        archive_id: str,
        start_offset: int,
        end_offset: int,
        content: str,
    ) -> dict:
        row = {
            "archive_news_id": archive_id,
            "start_offset": start_offset,
            "end_offset": end_offset,
            "content": content,
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
        }
        res = self.client.table("archive_news_comments").insert(row).execute()
        return res.data[0]


    def list_comments(self, archive_id: str) -> list[dict]:
        res = (
            self.client.table("archive_news_comments")
            .select("*")
            .eq("archive_news_id", archive_id)
            .order("start_offset")
            .execute()
        )
        return res.data or []


    def update_comment(self, comment_id: str, *, content: str) -> dict:
        res = (
            self.client.table("archive_news_comments")
            .update({"content": content, "updated_at": utc_now().isoformat()})
            .eq("id", comment_id)
            .execute()
        )
        if not res.data:
            raise NotFoundError("주석을 찾을 수 없습니다.")
        return res.data[0]


    def delete_comment(self, comment_id: str) -> bool:
        self.client.table("archive_news_comments").delete().eq("id", comment_id).execute()
        return True
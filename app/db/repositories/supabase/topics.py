from __future__ import annotations
from app.core.errors import NotFoundError
from app.core.types import TopicStatus
from .base import utc_now


class TopicsMixin:
    """analysis_topics 테이블 관련 메서드."""

    def create_analysis_topic(self, *, job_id: str, topic_name: str) -> dict:
        row = {
            "job_id": job_id,
            "topic_name": topic_name,
            "status": TopicStatus.PENDING.value,
        }
        res = self.client.table("analysis_topics").insert(row).execute()
        return res.data[0]

    def update_analysis_topic_status(
        self,
        topic_id: str,
        status: TopicStatus,
        current_step: str | None = None,
        error_message: str | None = None,
        document_count: int | None = None,
        trend_count: int | None = None,
    ) -> dict:
        update: dict = {"status": status.value}

        if current_step is not None:
            update["current_step"] = current_step
        if error_message is not None:
            update["error_message"] = error_message
        if document_count is not None:
            update["document_count"] = document_count
        if trend_count is not None:
            update["trend_count"] = trend_count
        if status in {TopicStatus.COMPLETED, TopicStatus.FAILED}:
            update["completed_at"] = utc_now().isoformat()

        res = (
            self.client.table("analysis_topics")
            .update(update)
            .eq("id", topic_id)
            .execute()
        )
        return res.data[0]

    def _topic(self, topic_id: str) -> dict:
        res = (
            self.client.table("analysis_topics")
            .select("*")
            .eq("id", topic_id)
            .single()
            .execute()
        )
        if not res.data:
            raise NotFoundError("분석 주제를 찾을 수 없습니다.")
        return res.data
from __future__ import annotations
from app.core.errors import NotFoundError
from app.core.types import JobStatus, TopicStatus
from .base import utc_now


class JobsMixin:

    def create_analysis_job(
        self,
        *,
        user_id: str,
        period: str,
        result_limit: int,
        sources: list[str],
    ) -> dict:
        now = utc_now().isoformat()
        row = {
            "user_id": user_id,
            "status": JobStatus.PENDING.value,
            "period": period,
            "result_limit": result_limit,
            "sources": sources,
            "started_at": now,
        }
        res = self.client.table("analysis_jobs").insert(row).execute()
        return res.data[0]

    def update_analysis_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: str | None = None,
    ) -> dict:
        update = {"status": status.value}
        if error_message:
            update["error_message"] = error_message
        if status in {JobStatus.COMPLETED, JobStatus.PARTIAL_FAILED, JobStatus.FAILED}:
            update["completed_at"] = utc_now().isoformat()

        res = (
            self.client.table("analysis_jobs")
            .update(update)
            .eq("id", job_id)
            .execute()
        )
        return res.data[0]


    def get_job_status(self, job_id: str) -> dict:
        job_res = (
            self.client.table("analysis_jobs")
            .select("*")
            .eq("id", job_id)
            .single()
            .execute()
        )
        if not job_res.data:
            raise NotFoundError("분석 작업을 찾을 수 없습니다.")

        topics_res = (
            self.client.table("analysis_topics")
            .select("*")
            .eq("job_id", job_id)
            .execute()
        )
        job = job_res.data
        topics = topics_res.data or []
        progress = self._progress(job["status"], topics)

        return {"job": job, "topics": topics, "progress": progress}


    def get_job_result(self, job_id: str) -> dict:
        job_res = (
            self.client.table("analysis_jobs")
            .select("*")
            .eq("id", job_id)
            .single()
            .execute()
        )
        if not job_res.data:
            raise NotFoundError("분석 작업을 찾을 수 없습니다.")

        topics_res = (
            self.client.table("analysis_topics")
            .select("*")
            .eq("job_id", job_id)
            .execute()
        )
        topics = topics_res.data or []
        payload_topics = []

        for topic in topics:
            trends_res = (
                self.client.table("trends")
                .select("*")
                .eq("topic_id", topic["id"])
                .order("rank")
                .execute()
            )
            payload_topics.append({"topic": topic, "trends": trends_res.data or []})

        return {"job": job_res.data, "topics": payload_topics}


    def get_latest_result(self, user_id: str) -> dict:
        res = (
            self.client.table("analysis_jobs")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", [JobStatus.COMPLETED.value, JobStatus.PARTIAL_FAILED.value])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not res.data:
            raise NotFoundError("완료된 분석 결과가 없습니다.")
        return self.get_job_result(res.data[0]["id"])


    @staticmethod
    def _progress(status: str, topics: list[dict]) -> int:
        if status == JobStatus.COMPLETED.value:
            return 100
        if status == JobStatus.FAILED.value:
            return 0
        if not topics:
            return 0

        weights = {
            TopicStatus.PENDING: 0,
            TopicStatus.COLLECTING: 15,
            TopicStatus.CLEANING: 30,
            TopicStatus.CLUSTERING: 45,
            TopicStatus.SCORING: 60,
            TopicStatus.LLM_SUMMARIZING: 75,
            TopicStatus.SAVING: 90,
            TopicStatus.COMPLETED: 100,
            TopicStatus.FAILED: 100,
        }

        total = 0
        for topic in topics:
            try:
                status_enum = TopicStatus(topic["status"])
            except ValueError:
                status_enum = TopicStatus.PENDING
            total += weights.get(status_enum, 0)

        return int(total / len(topics))
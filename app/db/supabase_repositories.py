from __future__ import annotations
from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

from app.core.errors import NotFoundError
from app.core.types import TopicStatus, JobStatus
from app.schemas.settings import UserSettingsResponse
from app.db.client import get_supabase_client


def utc_now() -> datetime:
    return datetime.now(UTC)


class SupabaseRepository:

    def __init__(self):
        self.client = get_supabase_client()

    # -------------------------
    # Jobs
    # -------------------------

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
            payload_topics.append({
                "topic": topic,
                "trends": trends_res.data or [],
            })

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

    # -------------------------
    # Topics
    # -------------------------

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

    # -------------------------
    # Trends
    # -------------------------

    def save_trends(
        self,
        *,
        topic_id: str,
        topic_name: str,
        trends: list[dict],
        period: str,
    ) -> list[dict]:
        saved = []

        for rank, trend in enumerate(trends, start=1):
            score = trend["scores"]
            if hasattr(score, "__dataclass_fields__"):
                score = {k: getattr(score, k) for k in score.__dataclass_fields__}

            # trends 테이블 저장
            trend_row = {
                "topic_id": topic_id,
                "title": trend["title"],
                "normalized_title": trend.get("normalized_title", trend["title"].strip().lower()),
                "rank": rank,
                "final_score": score.get("final_score", 0),
                "trend_momentum_score": score.get("trend_momentum_score", 0),
                "summary": trend.get("summary", ""),
                "detail_summary": trend.get("detail_summary", ""),
                "ai_comment": trend.get("ai_comment", ""),
                "keywords": trend.get("keywords", []),
                "trend_date": utc_now().date().isoformat(),
                "period": period,
            }
            trend_res = self.client.table("trends").insert(trend_row).execute()
            trend_id = trend_res.data[0]["id"]

            # trend_scores 테이블 저장
            score_row = {
                "trend_id": trend_id,
                "mention_score": score.get("mention_score", 0),
                "diversity_score": score.get("diversity_score", 0),
                "influence_score": score.get("influence_score", 0),
                "recency_score": score.get("recency_score", 0),
                "ai_importance_score": score.get("ai_importance_score", 0),
                "embedding_score": score.get("embedding_score", 0),       
                "trend_momentum_score": score.get("trend_momentum_score", 0),
                "final_score": score.get("final_score", 0),
            }
            self.client.table("trend_scores").insert(score_row).execute()

            daily_row = {
                "trend_id": trend_id,
                "trend_key": trend.get("normalized_title", trend["title"].strip().lower()),  # 추가
                "trend_title": trend["title"],                                                # 추가
                "topic_name": topic_name,                                                     # 추가
                "score_date": utc_now().date().isoformat(),                                   # 추가
                "trend_date": utc_now().date().isoformat(),
                "rank": rank,
                "final_score": score.get("final_score", 0),
                "trend_momentum_score": score.get("trend_momentum_score", 0),
            }
            self.client.table("trend_daily_scores").upsert(
                daily_row,
                on_conflict="trend_key,topic_name,score_date"
            ).execute()


            # trend_links 테이블 저장
            links = trend.get("links", [])
            if links:
                link_rows = [
                    {
                        "trend_id": trend_id,
                        "title": link.get("title", ""),
                        "url": link.get("url", ""),
                        "source_name": link.get("source_name", ""),
                        "source_type": link.get("source_type", "news"),
                        "author": link.get("author"),
                        "published_at": link.get("published_at").isoformat() 
                            if isinstance(link.get("published_at"), datetime) 
                            else link.get("published_at"),  
                        "summary": link.get("summary"),
                        "relevance_score": link.get("final_link_score"),
                        "credibility_score": link.get("credibility_score"),
                    }
                    for link in links
                ]
                self.client.table("trend_links").insert(link_rows).execute()

            saved.append(trend_res.data[0])

        self.update_analysis_topic_status(
            topic_id,
            TopicStatus.COMPLETED,
            "return_result",
            trend_count=len(saved),
        )
        return saved

    def get_trend_detail(self, trend_id: str) -> dict:
        trend_res = (
            self.client.table("trends")
            .select("*")
            .eq("id", trend_id)
            .single()
            .execute()
        )
        if not trend_res.data:
            raise NotFoundError("트렌드를 찾을 수 없습니다.")

        topic_res = (
            self.client.table("analysis_topics")
            .select("*")
            .eq("id", trend_res.data["topic_id"])
            .single()
            .execute()
        )
        scores_res = (
            self.client.table("trend_scores")
            .select("*")
            .eq("trend_id", trend_id)
            .single()
            .execute()
        )
        links_res = (
            self.client.table("trend_links")
            .select("*")
            .eq("trend_id", trend_id)
            .execute()
        )
        history_res = (
            self.client.table("trend_daily_scores")
            .select("trend_date, rank, final_score")
            .eq("trend_id", trend_id)
            .order("trend_date")
            .execute()
        )

        return {
            "trend": trend_res.data,
            "topic": topic_res.data,
            "scores": scores_res.data or {},
            "links": links_res.data or [],
            "rank_history": history_res.data or [],
        }

    # -------------------------
    # User Settings
    # -------------------------

    def get_user_settings(self, user_id: str) -> dict:
        res = (
            self.client.table("user_settings")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if not res.data:
            # 없으면 기본값으로 생성
            default = UserSettingsResponse(user_id=user_id).model_dump()
            return self.upsert_user_settings(default)
        return res.data

    def upsert_user_settings(self, settings: dict) -> dict:
        res = (
            self.client.table("user_settings")
            .upsert(settings, on_conflict="user_id")
            .execute()
        )
        return res.data[0]

    # -------------------------
    # 내부 헬퍼
    # -------------------------

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


# InMemory는 테스트용으로 유지
class InMemoryRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, dict] = {}
        self.topics: dict[str, dict] = {}
        self.trends: dict[str, dict] = {}
        self.scores: dict[str, dict] = {}
        self.links: dict[str, list[dict]] = {}
        self.settings: dict[str, dict] = {}

    def create_analysis_job(
        self,
        *,
        user_id: str,
        period: str,
        result_limit: int,
        sources: list[str],
    ) -> dict:
        job_id = f"job_{uuid4().hex[:12]}"
        now = utc_now()
        job = {
            "id": job_id,
            "user_id": user_id,
            "status": JobStatus.PENDING.value, 
            "period": period,
            "result_limit": result_limit,
            "sources": sources,
            "started_at": now,
            "completed_at": None,
            "error_message": None,
            "created_at": now,
        }
        self.jobs[job_id] = job
        return deepcopy(job)

    def update_analysis_job_status(
        self,
        job_id: str,
        status: JobStatus,          
        error_message: str | None = None,
    ) -> dict:
        job = self._job(job_id)
        job["status"] = status.value 
        if error_message:
            job["error_message"] = error_message
        if status in {               
            JobStatus.COMPLETED,
            JobStatus.PARTIAL_FAILED,
            JobStatus.FAILED,
        }:
            job["completed_at"] = utc_now()
        return deepcopy(job)

    def create_analysis_topic(self, *, job_id: str, topic_name: str) -> dict:
        self._job(job_id)
        topic_id = f"topic_{uuid4().hex[:12]}"
        now = utc_now()
        topic = {
            "id": topic_id,
            "job_id": job_id,
            "topic_name": topic_name,
            "status": "pending",
            "current_step": None,
            "document_count": 0,
            "trend_count": 0,
            "error_message": None,
            "started_at": None,
            "completed_at": None,
            "created_at": now,
        }
        self.topics[topic_id] = topic
        return deepcopy(topic)

    def update_analysis_topic_status(
        self,
        topic_id: str,
        status: TopicStatus,
        current_step: str | None = None,
        error_message: str | None = None,
        document_count: int | None = None,
        trend_count: int | None = None,
    ) -> dict:
        topic = self._topic(topic_id)
        topic["status"] = status.value
        topic["current_step"] = current_step
        if topic["started_at"] is None and status != "pending":
            topic["started_at"] = utc_now()
        if error_message:
            topic["error_message"] = error_message
        if document_count is not None:
            topic["document_count"] = document_count
        if trend_count is not None:
            topic["trend_count"] = trend_count
        if status in {TopicStatus.COMPLETED, TopicStatus.FAILED}:
            topic["completed_at"] = utc_now()
        return deepcopy(topic)

    def save_trends(self, *, topic_id: str, topic_name: str, trends: list[dict], period: str) -> list[dict]:
        self._topic(topic_id)
        saved: list[dict] = []
        now = utc_now()

        for rank, trend in enumerate(trends, start=1):
            trend_id = f"trend_{uuid4().hex[:12]}"
            score = trend["scores"]
            
            # Convert TrendScores dataclass to dict if needed
            if hasattr(score, "__dataclass_fields__"):
                score = {k: getattr(score, k) for k in score.__dataclass_fields__}
            
            row = {
                "id": trend_id,
                "topic_id": topic_id,
                "topic_name": topic_name,
                "title": trend["title"],
                "normalized_title": trend.get("normalized_title", trend["title"].strip().lower()),
                "rank": rank,
                "final_score": score.get("final_score", score["final_score"]) if isinstance(score, dict) else score["final_score"],
                "summary": trend.get("summary", ""),
                "detail_summary": trend.get("detail_summary", ""),
                "ai_comment": trend.get("ai_comment", ""),
                "keywords": trend.get("keywords", []),
                "trend_date": now.date().isoformat(),
                "period": period,
                "created_at": now,
            }

            self.trends[trend_id] = row
            self.scores[trend_id] = {"trend_id": trend_id, **score, "created_at": now}
            self.links[trend_id] = [
                {"trend_id": trend_id, "created_at": now, **link}
                for link in trend.get("links", [])
            ]
            saved.append(deepcopy(row))
        self.update_analysis_topic_status(topic_id, TopicStatus.COMPLETED, "return_result", trend_count=len(saved))
        return saved

    def get_job_status(self, job_id: str) -> dict:
        job = self._job(job_id)
        topics = [topic for topic in self.topics.values() if topic["job_id"] == job_id]
        progress = self._progress(job["status"], topics)
        return {"job": deepcopy(job), "topics": deepcopy(topics), "progress": progress}

    def get_job_result(self, job_id: str) -> dict:
        job = self._job(job_id)
        topics = [topic for topic in self.topics.values() if topic["job_id"] == job_id]
        payload_topics = []
        for topic in topics:
            trends = sorted(
                [trend for trend in self.trends.values() if trend["topic_id"] == topic["id"]],
                key=lambda item: item["rank"],
            )
            payload_topics.append({"topic": deepcopy(topic), "trends": deepcopy(trends)})
        return {"job": deepcopy(job), "topics": payload_topics}

    def get_trend_detail(self, trend_id: str) -> dict:
        trend = self._trend(trend_id)
        topic = self._topic(trend["topic_id"])
        return {
            "trend": deepcopy(trend),
            "topic": deepcopy(topic),
            "scores": deepcopy(self.scores.get(trend_id, {})),
            "links": deepcopy(self.links.get(trend_id, [])),
        }

    def get_latest_result(self, user_id: str) -> dict:
        completed = [
            job for job in self.jobs.values()
            if job["user_id"] == user_id
            and JobStatus(job["status"]) in { 
                JobStatus.COMPLETED,
                JobStatus.PARTIAL_FAILED,
            }
        ]
        if not completed:
            raise NotFoundError("완료된 분석 결과가 없습니다.")
        latest = max(completed, key=lambda item: item["created_at"])
        return self.get_job_result(latest["id"])

    def get_user_settings(self, user_id: str) -> dict:
        if user_id not in self.settings:
            self.settings[user_id] = UserSettingsResponse(user_id=user_id).model_dump()
        return deepcopy(self.settings[user_id])

    def upsert_user_settings(self, settings: dict) -> dict:
        self.settings[settings["user_id"]] = deepcopy(settings)
        return deepcopy(settings)

    def _job(self, job_id: str) -> dict:
        if job_id not in self.jobs:
            raise NotFoundError("분석 작업을 찾을 수 없습니다.")
        return self.jobs[job_id]

    def _topic(self, topic_id: str) -> dict:
        if topic_id not in self.topics:
            raise NotFoundError("분석 주제를 찾을 수 없습니다.")
        return self.topics[topic_id]

    def _trend(self, trend_id: str) -> dict:
        if trend_id not in self.trends:
            raise NotFoundError("트렌드를 찾을 수 없습니다.")
        return self.trends[trend_id]

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



repository = SupabaseRepository()
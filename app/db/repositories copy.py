#보관용
# from __future__ import annotations
# from copy import deepcopy
# from datetime import UTC, datetime
# from uuid import uuid4
# from app.core.errors import NotFoundError
# from app.schemas.settings import UserSettingsResponse
# from app.schemas.trends import TopicStatus
# from app.core.types import TopicStatus, JobStatus 


# def utc_now() -> datetime:
#     return datetime.now(UTC)

# class InMemoryRepository:
#     def __init__(self) -> None:
#         self.jobs: dict[str, dict] = {}
#         self.topics: dict[str, dict] = {}
#         self.trends: dict[str, dict] = {}
#         self.scores: dict[str, dict] = {}
#         self.links: dict[str, list[dict]] = {}
#         self.settings: dict[str, dict] = {}

#     def create_analysis_job(
#         self,
#         *,
#         user_id: str,
#         period: str,
#         result_limit: int,
#         sources: list[str],
#     ) -> dict:
#         job_id = f"job_{uuid4().hex[:12]}"
#         now = utc_now()
#         job = {
#             "id": job_id,
#             "user_id": user_id,
#             "status": JobStatus.PENDING.value, 
#             "period": period,
#             "result_limit": result_limit,
#             "sources": sources,
#             "started_at": now,
#             "completed_at": None,
#             "error_message": None,
#             "created_at": now,
#         }
#         self.jobs[job_id] = job
#         return deepcopy(job)

#     def update_analysis_job_status(
#         self,
#         job_id: str,
#         status: JobStatus,          
#         error_message: str | None = None,
#     ) -> dict:
#         job = self._job(job_id)
#         job["status"] = status.value 
#         if error_message:
#             job["error_message"] = error_message
#         if status in {               
#             JobStatus.COMPLETED,
#             JobStatus.PARTIAL_FAILED,
#             JobStatus.FAILED,
#         }:
#             job["completed_at"] = utc_now()
#         return deepcopy(job)

#     def create_analysis_topic(self, *, job_id: str, topic_name: str) -> dict:
#         self._job(job_id)
#         topic_id = f"topic_{uuid4().hex[:12]}"
#         now = utc_now()
#         topic = {
#             "id": topic_id,
#             "job_id": job_id,
#             "topic_name": topic_name,
#             "status": "pending",
#             "current_step": None,
#             "document_count": 0,
#             "trend_count": 0,
#             "error_message": None,
#             "started_at": None,
#             "completed_at": None,
#             "created_at": now,
#         }
#         self.topics[topic_id] = topic
#         return deepcopy(topic)

#     def update_analysis_topic_status(
#         self,
#         topic_id: str,
#         status: TopicStatus,
#         current_step: str | None = None,
#         error_message: str | None = None,
#         document_count: int | None = None,
#         trend_count: int | None = None,
#     ) -> dict:
#         topic = self._topic(topic_id)
#         topic["status"] = status.value
#         topic["current_step"] = current_step
#         if topic["started_at"] is None and status != "pending":
#             topic["started_at"] = utc_now()
#         if error_message:
#             topic["error_message"] = error_message
#         if document_count is not None:
#             topic["document_count"] = document_count
#         if trend_count is not None:
#             topic["trend_count"] = trend_count
#         if status in {TopicStatus.COMPLETED, TopicStatus.FAILED}:
#             topic["completed_at"] = utc_now()
#         return deepcopy(topic)

#     def save_trends(self, *, topic_id: str, topic_name: str, trends: list[dict], period: str) -> list[dict]:
#         self._topic(topic_id)
#         saved: list[dict] = []
#         now = utc_now()

#         for rank, trend in enumerate(trends, start=1):
#             trend_id = f"trend_{uuid4().hex[:12]}"
#             score = trend["scores"]
            
#             # Convert TrendScores dataclass to dict if needed
#             if hasattr(score, "__dataclass_fields__"):
#                 score = {k: getattr(score, k) for k in score.__dataclass_fields__}
            
#             row = {
#                 "id": trend_id,
#                 "topic_id": topic_id,
#                 "topic_name": topic_name,
#                 "title": trend["title"],
#                 "normalized_title": trend.get("normalized_title", trend["title"].strip().lower()),
#                 "rank": rank,
#                 "final_score": score.get("final_score", score["final_score"]) if isinstance(score, dict) else score["final_score"],
#                 "summary": trend.get("summary", ""),
#                 "detail_summary": trend.get("detail_summary", ""),
#                 "ai_comment": trend.get("ai_comment", ""),
#                 "keywords": trend.get("keywords", []),
#                 "trend_date": now.date().isoformat(),
#                 "period": period,
#                 "created_at": now,
#             }

#             self.trends[trend_id] = row
#             self.scores[trend_id] = {"trend_id": trend_id, **score, "created_at": now}
#             self.links[trend_id] = [
#                 {"trend_id": trend_id, "created_at": now, **link}
#                 for link in trend.get("links", [])
#             ]
#             saved.append(deepcopy(row))
#         self.update_analysis_topic_status(topic_id, TopicStatus.COMPLETED, "return_result", trend_count=len(saved))
#         return saved

#     def get_job_status(self, job_id: str) -> dict:
#         job = self._job(job_id)
#         topics = [topic for topic in self.topics.values() if topic["job_id"] == job_id]
#         progress = self._progress(job["status"], topics)
#         return {"job": deepcopy(job), "topics": deepcopy(topics), "progress": progress}

#     def get_job_result(self, job_id: str) -> dict:
#         job = self._job(job_id)
#         topics = [topic for topic in self.topics.values() if topic["job_id"] == job_id]
#         payload_topics = []
#         for topic in topics:
#             trends = sorted(
#                 [trend for trend in self.trends.values() if trend["topic_id"] == topic["id"]],
#                 key=lambda item: item["rank"],
#             )
#             payload_topics.append({"topic": deepcopy(topic), "trends": deepcopy(trends)})
#         return {"job": deepcopy(job), "topics": payload_topics}

#     def get_trend_detail(self, trend_id: str) -> dict:
#         trend = self._trend(trend_id)
#         topic = self._topic(trend["topic_id"])
#         return {
#             "trend": deepcopy(trend),
#             "topic": deepcopy(topic),
#             "scores": deepcopy(self.scores.get(trend_id, {})),
#             "links": deepcopy(self.links.get(trend_id, [])),
#         }

#     def get_latest_result(self, user_id: str) -> dict:
#         completed = [
#             job for job in self.jobs.values()
#             if job["user_id"] == user_id
#             and JobStatus(job["status"]) in { 
#                 JobStatus.COMPLETED,
#                 JobStatus.PARTIAL_FAILED,
#             }
#         ]
#         if not completed:
#             raise NotFoundError("완료된 분석 결과가 없습니다.")
#         latest = max(completed, key=lambda item: item["created_at"])
#         return self.get_job_result(latest["id"])

#     def get_user_settings(self, user_id: str) -> dict:
#         if user_id not in self.settings:
#             self.settings[user_id] = UserSettingsResponse(user_id=user_id).model_dump()
#         return deepcopy(self.settings[user_id])

#     def upsert_user_settings(self, settings: dict) -> dict:
#         self.settings[settings["user_id"]] = deepcopy(settings)
#         return deepcopy(settings)

#     def _job(self, job_id: str) -> dict:
#         if job_id not in self.jobs:
#             raise NotFoundError("분석 작업을 찾을 수 없습니다.")
#         return self.jobs[job_id]

#     def _topic(self, topic_id: str) -> dict:
#         if topic_id not in self.topics:
#             raise NotFoundError("분석 주제를 찾을 수 없습니다.")
#         return self.topics[topic_id]

#     def _trend(self, trend_id: str) -> dict:
#         if trend_id not in self.trends:
#             raise NotFoundError("트렌드를 찾을 수 없습니다.")
#         return self.trends[trend_id]

#     @staticmethod
#     def _progress(status: str, topics: list[dict]) -> int:
#         if status == JobStatus.COMPLETED.value:
#             return 100
#         if status == JobStatus.FAILED.value:
#             return 0
#         if not topics:
#             return 0

#         weights = {
#             TopicStatus.PENDING: 0,
#             TopicStatus.COLLECTING: 15,
#             TopicStatus.CLEANING: 30,
#             TopicStatus.CLUSTERING: 45,
#             TopicStatus.SCORING: 60,
#             TopicStatus.LLM_SUMMARIZING: 75,
#             TopicStatus.SAVING: 90,
#             TopicStatus.COMPLETED: 100,
#             TopicStatus.FAILED: 100,
#         }

#         total = 0

#         for topic in topics:
#             try:
#                 status_enum = TopicStatus(topic["status"])
#             except ValueError:
#                 status_enum = TopicStatus.PENDING

#             total += weights.get(status_enum, 0)

#         return int(total / len(topics))


# repository = InMemoryRepository()
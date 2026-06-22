from __future__ import annotations
from datetime import datetime
from app.core.errors import NotFoundError
from app.core.types import TopicStatus
from .base import utc_now


class TrendsMixin:
    """trends / trend_scores / trend_links / trend_daily_scores 관련 메서드."""

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
           saved = []

        # topic_id로 job_id 조회
        topic = self._topic(topic_id)
        job_id = topic["job_id"]

        for rank, trend in enumerate(trends, start=1):
            score = trend.get("scores", {}) or {}
            if hasattr(score, "__dataclass_fields__"):
                score = {k: getattr(score, k) for k in score.__dataclass_fields__}

            trend_row = {
                "job_id": job_id,  # ← 추가
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

            self._save_trend_score(trend_id, score)
            self._save_daily_score(trend_id, topic_name, trend, rank, score)
            self._save_trend_links(trend_id, trend.get("links", []))

            saved.append(trend_res.data[0])

        self.update_analysis_topic_status(
            topic_id,
            TopicStatus.COMPLETED,
            "return_result",
            trend_count=len(saved),
        )
        return saved


    def _save_trend_score(self, trend_id: str, score: dict) -> None:
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


    def _save_daily_score(
        self, trend_id: str, topic_name: str, trend: dict, rank: int, score: dict
    ) -> None:
        today = utc_now().date().isoformat()
        daily_row = {
            "trend_id": trend_id,
            "trend_key": trend.get("normalized_title", trend["title"].strip().lower()),
            "trend_title": trend["title"],
            "topic_name": topic_name,
            "score_date": today,
            "trend_date": today,
            "rank": rank,
            "final_score": score.get("final_score", 0),
            "trend_momentum_score": score.get("trend_momentum_score", 0),
        }
        self.client.table("trend_daily_scores").upsert(
            daily_row,
            on_conflict="trend_key,topic_name,score_date",
        ).execute()


    def _save_trend_links(self, trend_id: str, links: list[dict]) -> None:
        if not links:
            return

        link_rows = []

        for link in links:
            pub = link.get("published_at")

            link_rows.append({
                "trend_id": trend_id,
                "title": link.get("title", ""),
                "url": link.get("url", ""),
                "source_name": link.get("source_name", ""),
                "source_type": link.get("source_type", "news"),
                "author": link.get("author"),
                "published_at": pub.isoformat() if isinstance(pub, datetime) else pub,
                "summary": link.get("summary"),
                "relevance_score": link.get("final_link_score"),
                "credibility_score": link.get("credibility_score"),
            })

        self.client.table("trend_links").insert(link_rows).execute()


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
    
    
    def get_trends_by_topic_ids(self, topic_ids: list[str]):
        return (
            self.client.table("trends")
            .select("*")
            .in_("topic_id", topic_ids)
            .execute()
            .data
        )
    
    
    def get_links_by_trend_ids(self, trend_ids: list[str]):
        return (
            self.client.table("trend_links")
            .select("*")
            .in_("trend_id", trend_ids)
            .execute()
            .data
        )
    

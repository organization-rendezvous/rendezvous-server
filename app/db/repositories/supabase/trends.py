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
    

    def get_recent_trends_for_chat(
        self,
        *,
        keyword: str,
        limit: int = 10,
        days: int = 7,
    ) -> list[dict]:
        """
        News Chat용 내부 트렌드 검색.

        - 최근 N일(기본 7일) 이내 트렌드를 대상으로 한다.
        - title / summary / keywords 에 keyword가 포함된 항목을 조회한다.
        - trend_links 중 relevance_score 최고값 링크 1건을 url로 노출한다.

        추후 Supabase full-text search(to_tsvector / plainto_tsquery)로
        교체하면 정확도를 높일 수 있다.
        """
        from datetime import UTC, datetime, timedelta

        cutoff = (datetime.now(UTC) - timedelta(days=days)).date().isoformat()

        # 1. 최근 트렌드 조회
        trend_res = (
            self.client.table("trends")
            .select("id, title, summary, keywords, trend_date, final_score")
            .gte("trend_date", cutoff)
            .order("final_score", desc=True)
            .limit(50)
            .execute()
        )
        trends = trend_res.data or []

        # 2. trend_id 기준 중복 제거 (같은 트렌드가 여러 날짜로 저장된 경우 대비)
        seen_titles: set[str] = set()
        deduped: list[dict] = []
        for t in trends:
            norm = (t.get("title") or "").strip().lower()
            if norm not in seen_titles:
                seen_titles.add(norm)
                deduped.append(t)

        # 3. 키워드 필터 (Python side)
        kw = keyword.lower()
        matched = [
            t for t in deduped
            if kw in (t.get("title") or "").lower()
            or kw in (t.get("summary") or "").lower()
            or any(kw in k.lower() for k in (t.get("keywords") or []))
        ]

        if not matched:
            # 매칭 없으면 중복 제거된 전체에서 최신 순 limit개 반환
            matched = deduped[:limit]

        # 4. 상위 limit개 트렌드에 대표 링크 1건씩 붙이기 (url 있는 것만)
        trend_ids = [t["id"] for t in matched[:limit]]
        links_res = (
            self.client.table("trend_links")
            .select("trend_id, title, url, source_name, published_at, summary, relevance_score")
            .in_("trend_id", trend_ids)
            .neq("url", "")          # url 빈 행 제외
            .not_.is_("url", "null") # url null 행 제외
            .execute()
        )
        links_by_trend: dict[str, dict] = {}
        for link in (links_res.data or []):
            if not link.get("url"):  # 혹시 빈 문자열 통과한 경우 추가 방어
                continue
            tid = link["trend_id"]
            existing = links_by_trend.get(tid)
            if existing is None or (link.get("relevance_score") or 0) > (existing.get("relevance_score") or 0):
                links_by_trend[tid] = link

        # 5. 최종 반환 — url 없는 트렌드는 제외
        result = []
        for t in matched[:limit]:
            best_link = links_by_trend.get(t["id"])
            if not best_link:
                continue  # 유효한 링크가 없으면 카드로 노출하지 않음
            result.append({
                "id": t["id"],
                "title": t["title"],
                "summary": t.get("summary"),
                "keywords": t.get("keywords", []),
                "url": best_link["url"],
                "source_name": best_link.get("source_name"),
                "published_at": best_link.get("published_at"),
                "final_score": t.get("final_score", 0),
            })

        return result
    

    

    
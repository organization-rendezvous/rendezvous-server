#보관용

# from __future__ import annotations

# import logging
# from datetime import datetime

# logger = logging.getLogger(__name__)


# class WebSearchCollector:
#     """
#     팩트체크 / internal_hits 부족 시 fallback 웹 검색 컬렉터.

#     기존 collectors(news.py, rss.py)와 동일한 반환 dict 스키마를 유지한다:
#       title / url / source_name / source_type / summary / published_at

#     실제 검색 엔진 연동 전까지는 빈 리스트를 반환하는 stub으로 동작한다.
#     연동 시 이 클래스만 수정하면 workflow는 변경 없이 동작한다.
#     """

#     def search(self, query: str, *, limit: int = 5) -> list[dict]:
#         """
#         query로 웹 검색을 수행하고 표준화된 dict 목록을 반환한다.

#         반환 형식:
#         {
#             "title": str,
#             "url": str,
#             "source_name": str,
#             "source_type": "web",
#             "summary": str | None,
#             "published_at": str | None,   # ISO 8601
#         }
#         """
#         try:
#             return self._do_search(query, limit=limit)
#         except Exception as e:
#             logger.warning("WebSearchCollector 검색 실패 (query=%r): %s", query, e)
#             return []


#     def _do_search(self, query: str, *, limit: int) -> list[dict]:
#         """
#         실제 검색 엔진 연동 포인트.

#         TODO: SerpAPI / Tavily / DuckDuckGo API 등 연동 시 여기에 구현.
#         현재는 stub — 빈 리스트 반환.
#         """
#         logger.debug("WebSearchCollector stub 호출 (query=%r, limit=%d)", query, limit)
#         return []


#     @staticmethod
#     def _normalize(raw: dict) -> dict:
#         """외부 API 응답을 표준 스키마로 변환하는 헬퍼 (연동 시 활용)."""
#         pub = raw.get("published_at") or raw.get("date") or raw.get("publishedAt")
#         if isinstance(pub, datetime):
#             pub = pub.isoformat()

#         return {
#             "title": raw.get("title", ""),
#             "url": raw.get("url") or raw.get("link", ""),
#             "source_name": raw.get("source_name") or raw.get("source") or raw.get("domain", ""),
#             "source_type": "web",
#             "summary": raw.get("summary") or raw.get("snippet") or raw.get("description"),
#             "published_at": pub,
#         }
    

    
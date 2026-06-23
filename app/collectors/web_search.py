from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
import requests

logger = logging.getLogger(__name__)


class WebSearchCollector:
    """
    Tavily 기반 웹 검색 컬렉터
    """

    def search(self, query: str, *, limit: int = 5) -> list[dict]:
        try:
            return self._do_search(query, limit=limit)
        except Exception as e:
            logger.warning("WebSearchCollector 실패 (query=%r): %s", query, e)
            return []

    def _do_search(self, query: str, *, limit: int) -> list[dict]:
        api_key = os.getenv("TAVILY_API_KEY")  # <- 현재 환경 변수 유지

        if not api_key:
            logger.warning("TAVILY_API_KEY 없음")
            return []

        url = "https://api.tavily.com/search"

        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
            "max_results": limit,
        }

        res = requests.post(url, json=payload, timeout=10)

        if res.status_code != 200:
            logger.warning("Tavily API 실패: %s %s", res.status_code, res.text)
            return []

        data = res.json()

        results = []
        for item in data.get("results", [])[:limit]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source_name": "tavily",
                "source_type": "web",
                "summary": item.get("content"),
                "published_at": datetime.now(timezone.utc).isoformat(),
            })

        logger.debug("web search results=%d", len(results))
        return results
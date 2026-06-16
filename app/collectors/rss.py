import httpx
import feedparser
from datetime import datetime, UTC
from app.core.config import get_topic_keywords, parse_period


class RSSCollector:
    def __init__(self, url: str, source_name: str, source_type: str):
        self.url = url
        self.source_name = source_name
        self.source_type = source_type

    async def fetch(self, topic: str, period: str) -> list[dict]:
        keywords = get_topic_keywords(topic)
        cutoff = parse_period(period)

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(self.url)

            if res.status_code != 200:
                return []

        feed = feedparser.parse(res.text)

        if getattr(feed, "bozo", False):
            return []

        documents: list[dict] = []

        for entry in feed.entries:
            if not entry:
                continue

            title = getattr(entry, "title", "") or ""
            link = getattr(entry, "link", "") or ""

            if not link:
                continue

            # content safe parsing
            content = getattr(entry, "content", None)
            raw_text = ""
            if isinstance(content, list) and len(content) > 0:
                first = content[0]
                if isinstance(first, dict):
                    raw_text = first.get("value", "") or ""
            else:
                raw_text = getattr(entry, "summary", "") or ""

            summary = getattr(entry, "summary", "") or ""

            # keyword 필터
            searchable = (title + " " + summary + " " + raw_text).lower()
            if not any(kw in searchable for kw in keywords):
                continue

            # published_at safe parsing
            published_raw = getattr(entry, "published_parsed", None)
            published = None
            if published_raw and len(published_raw) >= 6:
                published = datetime(
                    published_raw[0],
                    published_raw[1],
                    published_raw[2],
                    published_raw[3],
                    published_raw[4],
                    published_raw[5],
                    tzinfo=UTC,
                )

            # 날짜 필터
            if published and published < cutoff:
                continue

            documents.append(
                {
                    "title": title,
                    "url": link,
                    "source_name": self.source_name,
                    "source_type": self.source_type,
                    "author": getattr(entry, "author", None),
                    "published_at": published,
                    "summary": summary,
                    "raw_text": raw_text,
                }
            )

        return documents
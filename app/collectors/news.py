import feedparser
from datetime import datetime, UTC
# from app.collectors.base import BaseCollector
from app.core.config import get_topic_keywords, parse_period


class NewsCollector:
    def __init__(self, feeds: list[str]):
        self.feeds = feeds

    def fetch(self, topic: str, period: str) -> list[dict]:
        now = datetime.now(UTC)
        cutoff = parse_period(period)
        keywords = get_topic_keywords(topic)
        results: list[dict] = []

        for url in self.feeds:
            feed = feedparser.parse(url)

            for entry in feed.entries[:30]:
                title = str(entry.get("title") or "")
                summary = str(entry.get("summary") or "")
                link = str(entry.get("link") or "")

                # keyword 필터
                searchable = (title + " " + summary).lower()
                if not any(kw in searchable for kw in keywords):
                    continue

                # 날짜 필터
                published = getattr(entry, "published_parsed", None)
                if published:
                    published_at = datetime(*published[:6], tzinfo=UTC)
                    if published_at < cutoff:
                        continue
                else:
                    published_at = now

                results.append(
                    {
                        "title": title,
                        "url": link,
                        "source_name": "News",
                        "source_type": "news",
                        "author": None,
                        "published_at": published_at,
                        "summary": summary[:300],
                        "raw_text": summary,
                    }
                )

        return results
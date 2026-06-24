import feedparser
from datetime import datetime, UTC

from app.core.config import (
    get_topic_keywords,
    parse_period,
)

from app.collectors.utils import (
    contains_keywords,
    parse_published,
    is_old_document,
    build_document,
)


class NewsCollector:
    def __init__(self, feeds: list[str]):
        self.feeds = feeds

    def fetch(
        self,
        topic: str,
        period: str,
    ) -> list[dict]:

        now = datetime.now(UTC)
        cutoff = parse_period(period)
        keywords = get_topic_keywords(topic)

        results: list[dict] = []

        for url in self.feeds:
            feed = feedparser.parse(url)

            for entry in feed.entries[:30]:
                title = str(
                    entry.get("title") or ""
                )

                summary = str(
                    entry.get("summary") or ""
                )

                link = str(
                    entry.get("link") or ""
                )

                if not contains_keywords(
                    f"{title} {summary}",
                    keywords,
                ):
                    continue

                published_at = parse_published(
                    getattr(
                        entry,
                        "published_parsed",
                        None,
                    )
                )

                if published_at:
                    if is_old_document(
                        published_at,
                        cutoff,
                    ):
                        continue
                else:
                    published_at = now

                results.append(
                    build_document(
                        title=title,
                        url=link,
                        source_name="News",
                        source_type="news",
                        author=None,
                        published_at=published_at,
                        summary=summary[:300],
                        raw_text=summary,
                    )
                )

        return results
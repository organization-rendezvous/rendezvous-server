import feedparser

from app.core.config import (
    get_topic_keywords,
    parse_period,
)

from app.collectors.utils import (
    contains_keywords,
    parse_published,
    is_old_document,
    build_document,
    fetch_html,
)


class RSSCollector:
    def __init__(
        self,
        url: str,
        source_name: str,
        source_type: str,
    ):
        self.url = url
        self.source_name = source_name
        self.source_type = source_type

    async def fetch(
        self,
        topic: str,
        period: str,
    ) -> list[dict]:

        keywords = get_topic_keywords(topic)
        cutoff = parse_period(period)

        html = await fetch_html(
            self.url,
            headers={
                "User-Agent": (
                    "Rendezvous/1.0 "
                    "trend-collector"
                )
            },
        )

        if not html:
            return []

        feed = feedparser.parse(html)

        if getattr(feed, "bozo", False):
            return []

        documents: list[dict] = []

        for entry in feed.entries:
            if not entry:
                continue

            title = getattr(
                entry,
                "title",
                "",
            ) or ""

            link = getattr(
                entry,
                "link",
                "",
            ) or ""

            if not link:
                continue

            content = getattr(
                entry,
                "content",
                None,
            )

            if (
                isinstance(content, list)
                and content
                and isinstance(
                    content[0],
                    dict,
                )
            ):
                raw_text = (
                    content[0].get(
                        "value",
                        "",
                    )
                    or ""
                )
            else:
                raw_text = getattr(
                    entry,
                    "summary",
                    "",
                ) or ""

            summary = getattr(
                entry,
                "summary",
                "",
            ) or ""

            if not contains_keywords(
                f"{title} {summary} {raw_text}",
                keywords,
            ):
                continue

            published = parse_published(
                getattr(
                    entry,
                    "published_parsed",
                    None,
                )
            )

            if is_old_document(
                published,
                cutoff,
            ):
                continue

            documents.append(
                build_document(
                    title=title,
                    url=link,
                    source_name=self.source_name,
                    source_type=self.source_type,
                    author=getattr(
                        entry,
                        "author",
                        None,
                    ),
                    published_at=published,
                    summary=summary,
                    raw_text=raw_text,
                )
            )

        return documents
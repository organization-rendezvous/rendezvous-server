from datetime import datetime, UTC

from bs4 import BeautifulSoup

from app.core.config import (
    get_topic_keywords,
)

from app.collectors.utils import (
    contains_keywords,
    build_document,
    fetch_html,
)


class OfficialCollector:
    def __init__(
        self,
        url: str,
        source_name: str,
    ):
        self.url = url
        self.source_name = source_name

    async def fetch(
        self,
        topic: str,
        period: str,
    ) -> list[dict]:

        keywords = get_topic_keywords(
            topic
        )

        html = await fetch_html(
            self.url
        )

        if not html:
            return []

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        articles = soup.select(
            "article a"
        )

        documents: list[dict] = []

        for a in articles[:20]:
            title = a.text.strip()

            link = str(
                a.get("href") or ""
            )

            if (
                not link
                or not link.startswith(
                    "http"
                )
            ):
                continue

            if not contains_keywords(
                title,
                keywords,
            ):
                continue

            documents.append(
                build_document(
                    title=title,
                    url=link,
                    source_name=self.source_name,
                    source_type="official_blog",
                    author=None,
                    published_at=datetime.now(
                        UTC
                    ),
                    summary=title,
                    raw_text=title,
                )
            )

        return documents
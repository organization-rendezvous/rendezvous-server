#보관용
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, UTC
from app.core.config import get_topic_keywords


class OfficialCollector:
    def __init__(self, url: str, source_name: str):
        self.url = url
        self.source_name = source_name

    async def fetch(self, topic: str, period: str) -> list[dict]:
        keywords = get_topic_keywords(topic)

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(self.url)

        if res.status_code != 200:
            return []

        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.select("article a")
        docs: list[dict] = []

        for a in articles[:20]:
            title = a.text.strip()
            link = str(a.get("href") or "")

            if not link or not link.startswith("http"):
                continue

            # keyword 필터
            if not any(kw in title.lower() for kw in keywords):
                continue

            docs.append(
                {
                    "title": title,
                    "url": link,
                    "source_name": self.source_name,
                    "source_type": "official_blog",
                    "author": None,
                    "published_at": datetime.now(UTC),
                    "summary": title,
                    "raw_text": title,
                }
            )

        return docs
    

    
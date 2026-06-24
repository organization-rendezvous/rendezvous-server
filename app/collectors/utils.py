from datetime import datetime, UTC

import httpx


def contains_keywords(
    text: str,
    keywords: list[str],
) -> bool:
    searchable = text.lower()

    return any(
        kw.lower() in searchable
        for kw in keywords
    )


def parse_published(parsed):
    if not parsed or len(parsed) < 6:
        return None

    return datetime(
        parsed[0],
        parsed[1],
        parsed[2],
        parsed[3],
        parsed[4],
        parsed[5],
        tzinfo=UTC,
    )


def is_old_document(
    published_at: datetime | None,
    cutoff: datetime,
) -> bool:
    return (
        published_at is not None
        and published_at < cutoff
    )


def build_document(
    *,
    title: str,
    url: str,
    source_name: str,
    source_type: str,
    author: str | None,
    published_at,
    summary: str,
    raw_text: str,
):
    return {
        "title": title,
        "url": url,
        "source_name": source_name,
        "source_type": source_type,
        "author": author,
        "published_at": published_at,
        "summary": summary,
        "raw_text": raw_text,
    }


async def fetch_html(
    url: str,
    *,
    headers: dict | None = None,
    timeout: int = 10,
) -> str | None:

    async with httpx.AsyncClient(
        timeout=timeout,
        headers=headers,
    ) as client:

        res = await client.get(url)

        if res.status_code != 200:
            return None

        return res.text



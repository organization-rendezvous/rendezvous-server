import hashlib
import re
from difflib import SequenceMatcher

from app.models.document import Document


def clean_documents(raw_documents: list[Document]) -> list[dict]:
    cleaned: list[dict] = []
    seen_urls: set[str] = set()
    seen_titles: list[str] = []

    for document in raw_documents:
        title = _normalize_text(document.title)
        url = document.url.strip()
        body = _normalize_text(f"{document.summary} {document.raw_text}")
        if not title or not url or len(body) < 30:
            continue
        if url in seen_urls or _has_similar_title(title, seen_titles):
            continue

        seen_urls.add(url)
        seen_titles.append(title)
        payload = document.model_dump()
        payload.update(
            {
                "title": title,
                "url": url,
                "source_name": _normalize_text(document.source_name),
                "source_type": document.source_type.lower().strip(),
                "summary": _normalize_text(document.summary),
                "raw_text": _normalize_text(document.raw_text),
                "content_hash": hashlib.sha256(f"{title}|{url}|{body}".encode()).hexdigest(),
            }
        )
        cleaned.append(payload)
    return cleaned


def _normalize_text(value: str | None) -> str:
    value = value or ""
    value = re.sub(r"[\u200b\xa0]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _has_similar_title(title: str, previous_titles: list[str]) -> bool:
    normalized = title.lower()
    return any(SequenceMatcher(None, normalized, other.lower()).ratio() >= 0.92 for other in previous_titles)

import asyncio
import inspect
from app.collectors.rss import RSSCollector
from app.collectors.official import OfficialCollector
from app.collectors.news import NewsCollector
from app.core.config import RSS_SOURCES, OFFICIAL_SOURCES, NEWS_SOURCES

def _build_collectors():
    collectors = []

    for url, name, stype in RSS_SOURCES["rss"]:
        collectors.append(("rss", RSSCollector(url, name, stype)))

    for url, name in OFFICIAL_SOURCES["official_blog"]:
        collectors.append(("official_blog", OfficialCollector(url, name)))

    collectors.append(("news", NewsCollector(NEWS_SOURCES["news"])))

    return collectors


async def _safe_fetch(
    collector,
    source_type: str,
    topic: str,
    period: str,
    documents: list,
    errors: list,
):
    try:
        if inspect.iscoroutinefunction(getattr(collector, "fetch", None)):
            docs = await collector.fetch(topic, period) or []
        else:
            docs = await asyncio.to_thread(collector.fetch, topic, period) or []
        documents.extend(docs)

    except Exception as e:
        print(traceback.format_exc()) 
        
        errors.append({
            "source": source_type,
            "message": str(e),
        })


async def collect_documents(topic: str, period: str, sources: list[str]) -> dict:
    documents = []
    errors = []
    tasks = []

    collectors = _build_collectors()

    for source in sources:
        for source_type, collector in collectors:
            if source != source_type:
                continue

            tasks.append(
                _safe_fetch(collector, source_type, topic, period, documents, errors)
            )

    if tasks:
        await asyncio.gather(*tasks)

    if not documents and not errors:
        documents = [
            {
                "title": "AI 트렌드 예시",
                "url": "https://example.com/ai-trend",
                "source_name": "Fallback",
                "source_type": "rss",
                "author": None,
                "published_at": None,
                "summary": "AI 기술이 급성장하고 있습니다.",
                "raw_text": "AI 기술 관련 뉴스 요약입니다.",
            }
        ]

    return {
        "documents": documents,
        "errors": errors,
    }



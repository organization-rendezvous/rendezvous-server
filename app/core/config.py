from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime, timedelta, UTC
from app.core.types import PipelineStep

#자료 키워드 관리
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "개발": [
        "developer", "dev", "programming", "coding",
        "software", "backend", "frontend",
        "api", "framework", "github", "open source",
        "system design", "engineering"
    ],

    "AI": [
        "ai", "artificial intelligence", "machine learning",
        "llm", "gpt", "chatgpt", "openai",
        "claude", "gemini", "deep learning",
        "model", "neural network"
    ],

    "문화/생활": [
        "culture", "lifestyle", "entertainment",
        "music", "movie", "drama", "fashion",
        "trend", "social media", "celebrity",
        "youtube", "instagram", "tiktok"
    ],

    "사회": [
        "society", "politics", "education",
        "economy", "labor", "health",
        "crime", "policy", "government",
        "issue", "report", "news"
    ],

    "국제": [
        "world", "international", "global",
        "usa", "china", "europe",
        "war", "diplomacy", "un",
        "economy global", "geopolitics"
    ],
}

RSS_SOURCES = {
    "rss": [
        ("https://www.theverge.com/rss/index.xml", "The Verge", "rss"),
        ("https://techcrunch.com/feed/", "TechCrunch", "rss"),
    ]
}

OFFICIAL_SOURCES = {
    "official_blog": [
        ("https://blog.google/", "Google Blog"),
    ]
}

NEWS_SOURCES = {
    "news": [
        "https://www.theverge.com/rss/index.xml",
        "https://techcrunch.com/feed/",
    ]
}



def get_topic_keywords(topic: str) -> list[str]:
    """topic 한글/영문명 → 검색 키워드 리스트 반환. 매핑 없으면 topic 자체를 키워드로 사용."""
    return TOPIC_KEYWORDS.get(topic.lower(), [topic.lower()])

def parse_period(period: str) -> datetime:
    """'24h', '7d', '30d' → cutoff datetime 반환. 파싱 실패 시 24h 기본값."""
    now = datetime.now(UTC)
    mapping = {
        "24h": timedelta(hours=24),
        "7d":  timedelta(days=7),
        "30d": timedelta(days=30),
    }
    return now - mapping.get(period, timedelta(hours=24))


#파이프라인 진행도 설정
STEP_PROGRESS_MAP = {
    PipelineStep.EMBEDDING: 10,
    PipelineStep.COLLECTING: 20,
    PipelineStep.CLEANING: 30,
    PipelineStep.CLUSTERING: 50,
    PipelineStep.SCORING: 65,
    PipelineStep.LLM_SUMMARIZING: 85,
    PipelineStep.SAVING: 95,
}

#환경번수 설정
class Settings(BaseSettings):
    app_name: str = "Rendezvous API"
    app_env: str = "local"
    app_debug: bool = True
    api_prefix: str = "/api"
    frontend_origin: str = "http://localhost:5173"
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    openai_api_key: str | None = None
    default_user_id: str = "personal-user"
    default_period: str = "24h"
    default_result_limit: int = 5
    default_topics: list[str] = ["개발", "AI", "문화/생활", "사회", "국제"]
    default_sources: list[str] = ["rss", "official_blog", "news"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

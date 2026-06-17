from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime, timedelta, UTC
from app.core.types import PipelineStep

#자료 키워드 관리
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "개발": [
        "developer", "devtools", "ide", "github", "programming", "coding",
        "framework", "sdk", "cli", "vscode", "tooling", "opensource",
        "개발", "프레임워크", "오픈소스", "라이브러리", "백엔드", "프론트엔드",
        "데브옵스", "쿠버네티스", "도커", "deployment", "cicd", "git",
    ],
    "ai": [
        "artificial intelligence", "llm", "machine learning", "gpt",
        "chatgpt", "openai", "claude", "gemini", "copilot", "deepmind",
        "인공지능", "머신러닝", "딥러닝", "생성형", "거대언어모델",
        "neural network", "transformer", "diffusion", "sora", "midjourney",
    ],
    "문화/생활": [
        "culture", "lifestyle", "entertainment", "food", "travel", "fashion",
        "health", "wellness", "movie", "music", "game", "sport",
        "문화", "생활", "여행", "음식", "패션", "건강", "영화", "음악", "게임",
        "라이프스타일", "취미", "공연", "전시",
    ],
    "사회": [
        "society", "education", "welfare", "environment", "policy",
        "government", "community", "labor", "housing", "crime", "accident",
        "사회", "교육", "복지", "환경", "정책", "정부", "노동", "주거", "공동체",
        "사건", "사고", "범죄", "법원", "검찰", "사고", "문제", 
    ],
    "국제": [
        "international", "global", "foreign", "diplomacy", "trade",
        "geopolitics", "war", "conflict", "united nations", "nato",
        "국제", "외교", "무역", "지정학", "전쟁", "분쟁", "해외", "미국", "중국",
        "유럽", "러시아", "중동", "sanctions", "summit",
    ],
}

RSS_SOURCES = {
    "rss": [
        # 개발
        ("https://techcrunch.com/feed/", "TechCrunch", "rss"),
        ("https://www.theverge.com/rss/index.xml", "The Verge", "rss"),
        ("https://feeds.feedburner.com/zdnet/korea", "ZDNet Korea", "rss"),
        ("https://www.etnews.com/rss/allArticleRss.xml", "전자신문", "rss"),
        ("https://news.google.com/rss/search?q=개발&hl=ko&gl=KR&ceid=KR:ko", "구글 뉴스(개발)", "rss"),
        # AI
        ("https://www.aitimes.com/rss/allArticle.xml", "AI타임스", "rss"),
        ("https://news.google.com/rss/search?q=인공지능&hl=ko&gl=KR&ceid=KR:ko", "구글 뉴스(AI)", "rss"),
        # 문화/생활
        ("https://rss.donga.com/culture.xml", "동아 문화", "rss"),
        # 사회
        ("https://rss.donga.com/society.xml", "동아 사회", "rss"),
        ("https://www.hani.co.kr/rss/society/", "한겨레 사회", "rss"),
        ("https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko", "구글 뉴스(전체)", "rss"),
        # 국제
        ("https://rss.donga.com/inter.xml", "동아 국제", "rss"),
        ("https://www.hani.co.kr/rss/international/", "한겨레 국제", "rss"),
        ("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC World", "rss"),
    ]
}

OFFICIAL_SOURCES = {
    "official_blog": [
        ("https://blog.google/", "Google Blog"),
        ("https://engineering.fb.com/", "Meta Engineering"),
        ("https://kakao.ai/blog", "카카오 AI 블로그"),
    ]
}


NEWS_SOURCES = {
    "news": [
        # 연합뉴스
        "https://www.yna.co.kr/rss/news.xml",          # 전체
        "https://www.yna.co.kr/rss/it.xml",            # IT
        # 조선일보
        "https://www.chosun.com/arc/outboundfeeds/rss/",
        # MBC
        "https://imnews.imbc.com/rss/news/news_00.xml",
        # KBS
        "https://news.kbs.co.kr/rss/rss.do?source=",
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
    PipelineStep.COLLECTING: 20,
    PipelineStep.CLEANING: 30,
    PipelineStep.CLUSTERING: 50,
    PipelineStep.EMBEDDING: 65,
    PipelineStep.SCORING: 75,
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

    #llm모델 정리
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

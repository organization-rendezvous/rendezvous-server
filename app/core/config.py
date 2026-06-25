from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime, timedelta, UTC
from app.core.types import PipelineStep

#자료 키워드 관리
TOPIC_KEYWORDS: dict[str, list[str]] = {
        "개발": [
        # 영어  
        "software", "backend", "frontend", "fullstack", "devops", "infrastructure",
        "kubernetes", "docker", "terraform", "ansible", "jenkins", "github actions",
        "rest api", "graphql", "microservice", "monorepo", "typescript", "python",
        "rust", "golang", "java", "kotlin", "swift", "react", "nextjs", "vue",
        "linux", "terminal", "shell", "npm", "package manager", "dependency",
        "testing", "unit test", "integration test", "performance", "optimization",
        "architecture", "design pattern", "database", "orm", "migration",
        # 한국어  
        "타입스크립트", "파이썬", "러스트", "고랭", "스위프트", "리액트",
        "인프라", "테스트", "배포", "빌드", "컨테이너", "서버리스",
        "데이터베이스", "쿼리", "최적화", "아키텍처", "디자인패턴",
        "패키지", "의존성", "모노레포", "터미널", "쉘스크립트",
    ],

    "ai": [
        # 영어  
        "anthropic", "mistral", "llama", "grok", "perplexity", "cursor", "devin",
        "multimodal", "vision model", "text to image", "text to video", "tts",
        "speech recognition", "embedding", "vector database", "langchain",
        "langgraph", "llamaindex", "inference", "quantization", "lora",
        "reinforcement learning", "rlhf", "alignment", "safety", "hallucination",
        "context window", "token", "benchmark", "eval", "ai assistant",
        "autonomous agent", "tool use", "function calling", "mcp",
        # 한국어  
        "멀티모달", "임베딩", "벡터", "추론", "파인튜닝", "정렬",
        "환각", "컨텍스트", "벤치마크", "평가", "에이전트", "자율",
        "텍스트 생성", "이미지 생성", "영상 생성", "음성 합성",
        "검색 증강", "지식 그래프", "온디바이스", "경량화",
    ],
    "문화/생활": [
        # 영어
        "culture", "lifestyle", "entertainment", "food", "travel", "fashion",
        "health", "wellness", "movie", "music", "game", "sport",
        "festival", "exhibition", "concert", "restaurant", "recipe",
        "fitness", "mental health", "hobby", "streaming",
        # 한국어
        "문화", "생활", "여행", "음식", "패션", "건강", "영화", "음악", "게임",
        "라이프스타일", "취미", "공연", "전시", "맛집", "레시피", "스포츠",
        "헬스", "뷰티", "인테리어", "반려동물", "육아", "웰빙",
    ],
    "사회": [
        # 영어 — 정부·정책·사회구조 중심
        "education", "welfare", "environment", "policy", "government",
        "community", "labor", "housing", "public health", "inequality",
        "human rights", "election", "legislation", "protest", "demographics",
        "social issue", "reform", "regulation", "ministry", "parliament",
        # 한국어 — 정부·정책·사회구조 중심
        "교육", "복지", "환경", "정책", "정부", "노동", "주거", "공동체",
        "저출생", "고령화", "의료", "복지정책", "선거", "입법", "시위",
        "인권", "차별", "규제", "법안", "국회", "장관", "행정",
        "사회문제", "불평등", "공공",
    ],
    "사건사고": [
        # 영어 — 사건·사고·논란 중심
        "accident", "incident", "disaster", "crime", "murder", "robbery",
        "assault", "fraud", "scandal", "controversy", "arrest", "investigation",
        "shooting", "explosion", "fire", "flood", "earthquake", "collapse",
        "crash", "missing", "victim", "suspect", "lawsuit", "abuse",
        "leak", "breach", "recall",
        # 한국어 — 사건·사고·논란 중심
        "사건", "사고", "재난", "범죄", "살인", "강도", "폭행", "사기",
        "스캔들", "논란", "체포", "수사", "구속", "기소", "피의자", "피해자",
        "화재", "폭발", "붕괴", "침수", "지진", "교통사고", "실종",
        "구조", "리콜", "유출", "해킹", "갑질", "폭로", "고발",
    ],
    "국제": [
        # 영어
        "international", "global", "foreign", "diplomacy", "trade",
        "geopolitics", "war", "conflict", "united nations", "nato",
        "sanctions", "summit", "bilateral", "multilateral", "treaty",
        "foreign policy", "humanitarian", "refugee", "g7", "g20",
        # 한국어
        "국제", "외교", "무역", "지정학", "전쟁", "분쟁", "해외", "미국", "중국",
        "유럽", "러시아", "중동", "일본", "북한", "정상회담", "제재",
        "협약", "동맹", "난민", "글로벌 이슈",
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
        ("https://www.youtube.com/feeds/videos.xml?channel_id=UC295-Dw0tDd-MTaG6-OQMBA", "Theo - t3.gg", "rss"),
        ("https://www.youtube.com/feeds/videos.xml?channel_id=UCUpJs89fSBXNolQGOYKn0YQ", "노마드코더", "rss"),
        ("https://www.reddit.com/r/programming/.rss", "r/programming", "rss"),
        ("https://www.reddit.com/r/webdev/.rss", "r/webdev", "rss"),
        ("https://www.reddit.com/r/devops/.rss", "r/devops", "rss"),

        # AI
        ("https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg", "Two Minute Papers", "rss"),
        ("https://www.aitimes.com/rss/allArticle.xml", "AI타임스", "rss"),
        ("https://news.google.com/rss/search?q=인공지능&hl=ko&gl=KR&ceid=KR:ko", "구글 뉴스(AI)", "rss"),
        ("https://www.youtube.com/feeds/videos.xml?channel_id=UCXUPKJO5MZQN11PqgIvyuvQ", "Andrej Karpathy", "rss"),
        ("https://www.reddit.com/r/MachineLearning/.rss", "r/MachineLearning", "rss"),
        ("https://www.reddit.com/r/LocalLLaMA/.rss", "r/LocalLLaMA", "rss"),
        ("https://www.reddit.com/r/artificial/.rss", "r/artificial", "rss"),
        
        # 문화/생활
        ("https://rss.donga.com/culture.xml", "동아 문화", "rss"),
        ("https://www.reddit.com/r/korea/.rss", "r/korea", "rss"),           # 한국 문화/생활 영어권 커뮤니티
        ("https://www.reddit.com/r/gaming/.rss", "r/gaming", "rss"),         # 게임
        ("https://www.reddit.com/r/movies/.rss", "r/movies", "rss"),         # 영화
        ("https://www.reddit.com/r/music/.rss", "r/music", "rss"),           # 음악

        # 사회
        ("https://rss.donga.com/society.xml", "동아 사회", "rss"),
        ("https://www.hani.co.kr/rss/society/", "한겨레 사회", "rss"),
        ("https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko", "구글 뉴스(전체)", "rss"),
        ("https://www.reddit.com/r/worldnews/.rss", "r/worldnews", "rss"),   # 글로벌 사회 이슈
        ("https://www.reddit.com/r/environment/.rss", "r/environment", "rss"), # 환경

        # 국제
        ("https://rss.donga.com/inter.xml", "동아 국제", "rss"),
        ("https://www.hani.co.kr/rss/international/", "한겨레 국제", "rss"),
        ("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC World", "rss"),
        ("https://www.reddit.com/r/geopolitics/.rss", "r/geopolitics", "rss"), # 지정학
        ("https://www.reddit.com/r/europe/.rss", "r/europe", "rss"),           # 유럽
    ]
}

OFFICIAL_SOURCES = {
    "official_blog": [
        # AI
        ("https://openai.com/news/", "OpenAI"),
        ("https://www.anthropic.com/news", "Anthropic"),
        ("https://huggingface.co/blog", "HuggingFace"),
        ("https://mistral.ai/news", "Mistral"),
        ("https://cohere.com/blog", "Cohere"),

        # Google
        ("https://blog.google/", "Google Blog"),
        ("https://developers.googleblog.com/", "Google Developers"),
        ("https://research.google/blog/", "Google Research"),
        ("https://deepmind.google/discover/blog/", "Google DeepMind"),

        # Meta
        ("https://engineering.fb.com/", "Meta Engineering"),
        ("https://ai.meta.com/blog/", "Meta AI"),

        # Microsoft
        ("https://devblogs.microsoft.com/", "Microsoft DevBlogs"),
        ("https://blogs.microsoft.com/ai/", "Microsoft AI"),

        # AWS
        ("https://aws.amazon.com/blogs/aws/", "AWS News"),
        ("https://aws.amazon.com/blogs/machine-learning/", "AWS ML"),
        ("https://aws.amazon.com/blogs/architecture/", "AWS Architecture"),

        # Cloud
        ("https://cloud.google.com/blog", "Google Cloud"),
        ("https://blog.cloudflare.com/", "Cloudflare"),
        ("https://www.databricks.com/blog", "Databricks"),

        # Developer Platform
        ("https://github.blog/", "GitHub"),
        ("https://vercel.com/blog", "Vercel"),
        ("https://stripe.com/blog", "Stripe"),
        ("https://shopify.engineering/", "Shopify"),
        ("https://slack.engineering/", "Slack"),

        # Infra
        ("https://netflixtechblog.com/", "Netflix"),
        ("https://eng.uber.com/", "Uber"),
        ("https://discord.com/blog/tag/engineering", "Discord"),
        ("https://engineering.atspotify.com/", "Spotify"),
        ("https://www.figma.com/blog/engineering/", "Figma"),
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

#자료 최대 글짜 수
MAX_EMBEDDING_CHARS = 4000



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

#기본 유저 id설정
DEFAULT_USER = "personal-user"


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


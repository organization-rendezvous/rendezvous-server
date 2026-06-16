from datetime import datetime
from pydantic import BaseModel, Field
from app.core.types import JobStatus, TopicStatus


class AnalyzeTrendRequest(BaseModel):
    user_id: str = "personal-user"
    topics: list[str] | None = None
    period: str | None = None
    result_limit: int | None = Field(default=None, ge=1, le=20)
    sources: list[str] | None = None


class AnalyzeTrendResponse(BaseModel):
    job_id: str
    status: JobStatus
    started_at: datetime


class AnalysisTopicStatusResponse(BaseModel):
    topic_id: str
    name: str
    status: TopicStatus
    current_step: str | None = None
    error_message: str | None = None


class AnalysisJobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    topics: list[AnalysisTopicStatusResponse]


class TrendSummaryItem(BaseModel):
    trend_id: str
    rank: int
    title: str
    summary: str
    score: float
    is_rising: bool = True


class TopicTrendResult(BaseModel):
    topic_id: str
    name: str
    trends: list[TrendSummaryItem]


class AnalysisJobResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    topics: list[TopicTrendResult]


class TrendScoreResponse(BaseModel):
    mention_score: float
    growth_score: float = 0
    diversity_score: float
    influence_score: float
    recency_score: float
    ai_importance_score: float
    final_score: float


class TrendLinkResponse(BaseModel):
    title: str
    url: str
    source_name: str
    source_type: str
    published_at: datetime | None = None
    summary: str | None = None
    relevance_score: float | None = None
    credibility_score: float | None = None


class TrendDetailResponse(BaseModel):
    trend_id: str
    title: str
    topic: str
    rank: int
    score: float
    summary: str
    detail_summary: str
    ai_comment: str
    keywords: list[str]
    scores: TrendScoreResponse
    links: list[TrendLinkResponse]

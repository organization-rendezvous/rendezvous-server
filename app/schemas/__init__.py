from app.schemas.common import ErrorResponse
from app.schemas.settings import UpdateUserSettingsRequest, UserSettingsResponse
from app.schemas.trends import (
    AnalysisJobResultResponse,
    AnalysisJobStatusResponse,
    AnalysisTopicStatusResponse,
    AnalyzeTrendRequest,
    AnalyzeTrendResponse,
    TopicTrendResult,
    TrendDetailResponse,
    TrendLinkResponse,
    TrendScoreResponse,
    TrendSummaryItem,
)

__all__ = [
    "AnalysisJobResultResponse",
    "AnalysisJobStatusResponse",
    "AnalysisTopicStatusResponse",
    "AnalyzeTrendRequest",
    "AnalyzeTrendResponse",
    "ErrorResponse",
    "TopicTrendResult",
    "TrendDetailResponse",
    "TrendLinkResponse",
    "TrendScoreResponse",
    "TrendSummaryItem",
    "UpdateUserSettingsRequest",
    "UserSettingsResponse",
]

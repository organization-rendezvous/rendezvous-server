from typing import TypedDict, Any

#입력 데이터의 구조를 정의하는 TypedDict
class TrendAnalysisInputState(TypedDict):
    job_id: str
    topic_id: str
    topic: str
    period: str
    result_limit: int
    sources: list[str]

#분석 과정에서 생성되는 데이터의 구조를 정의하는 TypedDict
class TrendAnalysisState(TypedDict):
    job_id: str
    topic_id: str
    topic: str
    period: str
    result_limit: int
    sources: list[str]

    raw_documents: list[dict]
    cleaned_documents: list[dict]

    trend_candidates: list[Any]
    scored_trends: list[Any]
    
    summarized_trends: list[Any]

    final_trends: list[Any]
    trend_embedding: list[float] | None

    errors: list[dict]
    retry_count: int
    next_action: str
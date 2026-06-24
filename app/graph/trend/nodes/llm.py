# 전체 트렌드 분석 workflow 상태 객체 정의
from app.graph.trend.state import TrendAnalysisState

# TopicStatus Enum
from app.core.types import TopicStatus

# LLM 기반 트렌드 재정렬 (reranking)
from app.llm.reranker import rerank_trends

# LLM 기반 트렌드 요약 batch 생성
from app.llm.summaries import generate_trend_summaries_batch

# 상태 업데이트 helper
from app.graph.common.helpers import update_status


def rerank_trends_node(
    state: TrendAnalysisState,
) -> TrendAnalysisState:
    """
    LLM 기반 재정렬 (선택 단계)
    """

    update_status(
       state,
        TopicStatus.LLM_SUMMARIZING,
        "rerank_trends",
    )

    state["scored_trends"] = rerank_trends(
        state.get(
            "scored_trends",
            [],
        ),
        state["topic"],
    )

    state["next_action"] = (
        "generate_llm_summary"
    )

    return state


def generate_llm_summary_node(
    state: TrendAnalysisState,
) -> TrendAnalysisState:
    """
    LLM 기반 트렌드 요약 생성 (batch)
    """
    update_status(
        state,
        TopicStatus.LLM_SUMMARIZING,  
        "generate_llm_summary"
    )

    state["summarized_trends"] = generate_trend_summaries_batch(
        state.get("scored_trends", []),
        state.get("topic")
    )

    state["next_action"] = "select_representative_links"

    return state


def enrich_llm_output_node(
    state: TrendAnalysisState,
) -> TrendAnalysisState:
    """LLM 결과와 기존 scoring 결과 merge (최종 정리 단계)"""

    update_status(
        state,
        TopicStatus.SAVING,
        "enrich_llm_output"
    )

    enriched = []

    for trend in state.get("summarized_trends", []):
        enriched.append({
            "title": trend.get("title", ""),
            "documents": trend.get("documents", []),
            "scores": trend.get("scores"),
            "embedding": trend.get("embedding"),
            "summary": trend.get("llm_summary", ""),
            "detail_summary": trend.get("llm_detail_summary", ""),
            "ai_comment": trend.get("llm_importance_reason", ""),
            "keywords": trend.get("keywords") or [],
        })

    state["final_trends"] = enriched
    state["next_action"] = "select_representative_links"
    return state
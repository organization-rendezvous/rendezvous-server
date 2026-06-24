# 전체 트렌드 분석 workflow 상태 객체 정의
from app.graph.trend.state import TrendAnalysisState

# TopicStatus Enum
from app.core.types import TopicStatus

# 트렌드 scoring (mention, embedding, recency, growth 등)
from app.scorers import score_trends

# 상태 업데이트 helper
from app.graph.common.helpers import update_status


def score_trends_node(
    state: TrendAnalysisState,
) -> TrendAnalysisState:
    """
    트렌드 후보 점수 계산 (mention, embedding, recency 등)
    """
    
    update_status(
        state,
        TopicStatus.SCORING, 
        "score_trends"
    )

    scored = score_trends(
        state["trend_candidates"],
        state["result_limit"]
    )

    state["scored_trends"] = scored
    state["next_action"] = "generate_llm_summary"

    return state
# 전체 트렌드 분석 workflow 상태 객체 정의
from app.graph.trend.state import TrendAnalysisState
# 분석 결과 저장 및 상태 업데이트
from app.db.repository_factory import repository
# TopicStatus Enum 
from app.core.types import TopicStatus
from app.graph.common.helpers import update_status

def save_result_node(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    최종 결과 DB 저장
    """
    update_status(
        state,
        TopicStatus.SAVING, 
        "save_result"
    )

    repository.save_trends(
        topic_id=state.get("topic_id"),
        topic_name=state.get("topic"),
        trends=state.get("final_trends", []),
        period=state.get("period"),
    )

    state["next_action"] = "return_result"

    return state

# 트렌드별 대표 링크 선정 로직
from app.services.trend.links import (
    select_representative_links,
)

# 전체 트렌드 분석 workflow 상태 객체 정의
from app.graph.trend.state import (
    TrendAnalysisState,
)

# TopicStatus Enum
from app.core.types import (
    TopicStatus,
)

# 상태 업데이트 helper
from app.graph.common.helpers import (
    update_status,
)


def select_representative_links_node(
    state: TrendAnalysisState,
) -> TrendAnalysisState:
    """
    각 트렌드별 대표 문서 링크 선정
    """
    trends = state.get("final_trends") or state.get("summarized_trends") or state.get("scored_trends", [])

    update_status(
        state,
        TopicStatus.SAVING,
        "select_representative_links"
    )

    state["final_trends"] = select_representative_links(trends)
    state["next_action"] = "save_result"
    return state
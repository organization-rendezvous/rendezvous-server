# 전체 트렌드 분석 workflow 상태 객체 정의
from app.graph.trend.state import TrendAnalysisState

# RSS / 공식 블로그 / 외부 소스에서 문서 수집
from app.collectors import collect_documents

# TopicStatus Enum
from app.core.types import TopicStatus

# 상태 업데이트 helper
from app.graph.common.helpers import update_status


async def collect_sources(
    state: TrendAnalysisState,
) -> TrendAnalysisState:
    """
    RSS / 공식 블로그 / 뉴스 등에서 원본 문서 수집
    """

    update_status(
       state,
        TopicStatus.COLLECTING,
        "collect_sources",
    )

    result = await collect_documents(
        state["topic"],
        state["period"],
        state["sources"],
    )

    state["raw_documents"] = (
        result["documents"]
    )

    state["errors"].extend(
        result["errors"]
    )

    state["next_action"] = (
        "clean_documents"
    )

    update_status(
        state,
        TopicStatus.COLLECTING,
        "collect_sources",
        document_count=len(
            state.get(
                "raw_documents",
                [],
            )
        ),
    )

    return state
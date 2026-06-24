from app.db.repository_factory import repository
from app.graph.trend.state import TrendAnalysisState
from app.core.types import TopicStatus
from app.graph.trend.nodes.collect import (
    collect_sources,
)
from app.graph.trend.nodes.clean import (
    clean_documents_node,
)
from app.graph.trend.nodes.candidate import (
    generate_candidates_node,
)
from app.graph.trend.nodes.embedding import (
    embed_candidates_node,
)
from app.graph.trend.nodes.scoring import (
    score_trends_node,
)
from app.graph.trend.nodes.llm import (
    generate_llm_summary_node,
    enrich_llm_output_node,
)
from app.graph.trend.nodes.links import (
    select_representative_links_node,
)
from app.graph.trend.nodes.save import (
    save_result_node,
)
from app.graph.common.helpers import update_status
import traceback



async def run_topic_analysis(
    state: TrendAnalysisState,
) -> TrendAnalysisState:
    """
    전체 트렌드 분석 workflow 실행
    """

    try:
        state = initialize_analysis(state)

        state = await collect_sources(state)
        state = clean_documents_node(state)
        state = generate_candidates_node(state)
        state = embed_candidates_node(state)
        state = score_trends_node(state)
        state = generate_llm_summary_node(state)
        state = enrich_llm_output_node(state)
        state = select_representative_links_node(state)
        state = save_result_node(state)

        return return_result(state)

    except Exception as exc:

        print("=" * 80)
        print(traceback.format_exc())
        print("=" * 80)

        repository.update_analysis_topic_status(
            state["topic_id"],
            TopicStatus.FAILED,
            state.get("next_action"),
            error_message=str(exc),
        )

        state.setdefault(
            "errors",
            [],
        ).append(
            {
                "stage": state.get(
                    "next_action",
                    "unknown",
                ),
                "message": str(exc),
            }
        )

        return state


def initialize_analysis(
    state: TrendAnalysisState,
) -> TrendAnalysisState:
    """
    workflow 초기 상태 세팅
    """

    state.setdefault(
        "raw_documents",
        [],
    )

    state.setdefault(
        "cleaned_documents",
        [],
    )

    state.setdefault(
        "trend_candidates",
        [],
    )

    state.setdefault(
        "scored_trends",
        [],
    )

    state.setdefault(
        "summarized_trends",
        [],
    )

    state.setdefault(
        "final_trends",
        [],
    )

    state.setdefault(
        "errors",
        [],
    )

    state["retry_count"] = 0
    state["next_action"] = "collect_sources"

    return state


def return_result(
    state: TrendAnalysisState,
) -> TrendAnalysisState:
    """
    workflow 완료 처리
    """

    update_status(
        state,
        TopicStatus.COMPLETED,
        "return_result",
        document_count=len(
            state.get(
                "cleaned_documents",
                [],
            )
        ),
        trend_count=len(
            state.get(
                "final_trends",
                [],
            )
        ),
    )

    return state
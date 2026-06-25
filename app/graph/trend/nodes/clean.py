# 문서 타입 정의
from app.models.document import Document

# 전체 트렌드 분석 workflow 상태 객체 정의
from app.graph.trend.state import TrendAnalysisState

# 문서 정제 로직 (중복 제거, normalization 등)
from app.analyzers.cleaner import clean_documents

# 문서 필터링 (topic 키워드 기반)
from app.analyzers.topic_filter import filter_documents_by_topic

# TopicStatus Enum
from app.core.types import TopicStatus

# 상태 업데이트 helper
from app.graph.common.helpers import update_status


def clean_documents_from_dicts(
    documents: list[dict],
) -> list[dict]:
    """
    dict → Document 변환 후 cleaner로 전달
    """
    return clean_documents(
        [
            Document(**d)
            for d in documents
        ]
    )


def clean_documents_node(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    중복 제거 / 텍스트 정규화 / topic 필터링 강화
    """
    docs = clean_documents_from_dicts(state["raw_documents"])

    filtered = filter_documents_by_topic(
        docs,
        state["topic"]
    )


    state["cleaned_documents"] = filtered

    update_status(
        state,
        TopicStatus.CLEANING,  
        "clean_documents"
    )

    state["next_action"] = "generate_candidates"
    return state
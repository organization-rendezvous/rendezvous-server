# 전체 트렌드 분석 workflow 상태 객체 정의
from app.graph.trend.state import TrendAnalysisState

# 문서 필터링 (topic 키워드 기반)
from app.analyzers.topic_filter import filter_documents_by_topic

# TopicStatus Enum
from app.core.types import TopicStatus

# OpenAI embedding 생성 클라이언트
from app.embeddings.client import embed_texts

# 문서 전처리 + dict → candidate 변환 (클러스터링 이전 단계)
from app.analyzers import generate_candidates

# embedding 기반 클러스터링 로직
from app.analyzers.cluster import cluster_candidates

# 상태 업데이트 helper
from app.graph.common.helpers import update_status
from app.core.config import MAX_EMBEDDING_CHARS


def generate_candidates_node(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    topic 기반 candidate 생성 (핵심 수정)
    """
    update_status(
        state,
        TopicStatus.CLUSTERING, 
        "generate_candidates"
    )

    cleaned_documents = state.get("cleaned_documents", [])

    cleaned_documents = filter_documents_by_topic(
        cleaned_documents,
        state["topic"]
    )

    texts = [
        (
            " ".join([
                doc.get("title", ""),
                doc.get("summary", ""),
                doc.get("raw_text", ""),
            ])
        )[:MAX_EMBEDDING_CHARS]
        for doc in cleaned_documents
    ]

    embeddings = embed_texts(texts) if texts else []

    documents_with_embeddings = [
        {**doc, "embedding": emb}
        for doc, emb in zip(cleaned_documents, embeddings)
    ]

    state["trend_candidates"] = generate_candidates(documents_with_embeddings)
    state["next_action"] = "embed_candidates"

    return state


def cluster_candidates_node(state):
    """
    (옵션 단계) embedding 기반 추가 클러스터링
    현재 pipeline에서는 비활성 가능
    """
    update_status(
        state,
        TopicStatus.CLUSTERING, 
        "cluster_candidates"
    )

    state["trend_candidates"] = cluster_candidates(state["trend_candidates"])
    state["next_action"] = "score_trends"

    return state
# 전체 트렌드 분석 workflow 상태 객체 정의
from app.graph.trend.state import TrendAnalysisState

# TopicStatus Enum
from app.core.types import TopicStatus

# OpenAI embedding 생성 클라이언트
from app.embeddings.client import embed_texts

# 상태 업데이트 helper
from app.graph.common.helpers import update_status


def embed_candidates_node(
    state: TrendAnalysisState,
) -> TrendAnalysisState:
    """후보 문서들 embedding 생성 + centroid 계산 (후속 scoring에서 활용) """

    update_status(
        state,
        TopicStatus.SCORING, 
        "embed_candidates"
    )

    candidates = state["trend_candidates"]

    texts = []
    for c in candidates:
        title = getattr(c, "title", "")
        keywords = getattr(c, "keywords", [])
        texts.append(title + " " + " ".join(keywords))

    embeddings = embed_texts(texts)

    for c, emb in zip(candidates, embeddings):
        if hasattr(c, "embedding"):
            setattr(c, "embedding", emb)

    centroid = []
    if embeddings:
        centroid = [sum(x)/len(x) for x in zip(*embeddings)]

    state["trend_candidates"] = candidates
    state["trend_embedding"] = centroid
    state["next_action"] = "score_trends"

    return state
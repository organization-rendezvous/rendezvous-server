
# 문서 전처리 + dict → candidate 변환 (클러스터링 이전 단계)
from app.analyzers import generate_candidates

# RSS / 공식 블로그 / 외부 소스에서 문서 수집
from app.collectors import collect_documents

# 분석 결과 저장 및 상태 업데이트 (DB 레이어, 현재는 InMemory 포함)
from app.db.repository_factory import repository

# 전체 트렌드 분석 workflow 상태 객체 정의
from app.graph.state import TrendAnalysisState

# 트렌드 scoring (mention, embedding, recency, growth 등)
from app.scorers import score_trends

# 트렌드별 대표 링크 선정 로직
from app.services.trend.links import select_representative_links

# LLM 기반 트렌드 요약 batch 생성
from app.llm.summaries import generate_trend_summaries_batch

# 문서 정제 로직 (중복 제거, normalization 등)
from app.analyzers.cleaner import clean_documents

# embedding 기반 클러스터링 로직
from app.analyzers.cluster import cluster_candidates

# LLM 기반 트렌드 재정렬 (reranking)
from app.llm.reranker import rerank_trends

# OpenAI embedding 생성 클라이언트
from app.embeddings.client import embed_texts

# 문서 타입 정의
from app.models.document import Document

# 문서 필터링 (topic 키워드 기반)
from app.analyzers.topic_filter import filter_documents_by_topic

# TopicStatus Enum 
from app.core.types import TopicStatus


async def run_topic_analysis(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    전체 트렌드 분석 workflow 실행 엔트리 포인트
    (수집 → 전처리 → 클러스터링 → embedding → scoring → LLM → 링크 → 저장)
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
        repository.update_analysis_topic_status(
            state["topic_id"],
            TopicStatus.FAILED,  
            state.get("next_action"),
            error_message=str(exc),
        )
        state.setdefault("errors", []).append({
            "stage": state.get("next_action", "unknown"),
            "message": str(exc)
        })
        return state


def initialize_analysis(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    workflow 초기 상태 세팅 (리스트 초기화, step 초기화)
    """
    state.setdefault("raw_documents", [])
    state.setdefault("cleaned_documents", [])
    state.setdefault("trend_candidates", [])
    state.setdefault("scored_trends", [])
    state.setdefault("summarized_trends", [])
    state.setdefault("final_trends", [])
    state.setdefault("errors", [])
    state["retry_count"] = 0
    state["next_action"] = "collect_sources"
    return state


async def collect_sources(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    RSS / 공식 블로그 / 뉴스 등에서 원본 문서 수집
    """
    repository.update_analysis_topic_status(
        state["topic_id"],
        TopicStatus.COLLECTING, 
        "collect_sources"
    )

    result = await collect_documents(state["topic"], state["period"], state["sources"])

    state["raw_documents"] = result["documents"]
    state["errors"].extend(result["errors"])
    state["next_action"] = "clean_documents"

    repository.update_analysis_topic_status(
        state.get("topic_id"),
        TopicStatus.COLLECTING,  
        "collect_sources",
        document_count=len(state.get("raw_documents", [])),
    )

    return state


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

    repository.update_analysis_topic_status(
        state.get("topic_id"),
        TopicStatus.CLEANING,  
        "clean_documents"
    )

    state["next_action"] = "generate_candidates"
    return state


def generate_candidates_node(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    topic 기반 candidate 생성 (핵심 수정)
    """
    repository.update_analysis_topic_status(
        state["topic_id"],
        TopicStatus.CLUSTERING, 
        "generate_candidates"
    )

    cleaned_documents = state.get("cleaned_documents", [])

    cleaned_documents = filter_documents_by_topic(
        cleaned_documents,
        state["topic"]
    )

    texts = [
        " ".join([
            doc.get("title", ""),
            doc.get("summary", ""),
            doc.get("raw_text", ""),
        ])
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


def embed_candidates_node(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    후보 문서들 embedding 생성 + centroid 계산
    (후속 scoring에서 활용)
    """
    repository.update_analysis_topic_status(
        state["topic_id"],
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


def cluster_candidates_node(state):
    """
    (옵션 단계) embedding 기반 추가 클러스터링
    현재 pipeline에서는 비활성 가능
    """
    repository.update_analysis_topic_status(
        state.get("topic_id"),
        TopicStatus.CLUSTERING, 
        "cluster_candidates"
    )

    state["trend_candidates"] = cluster_candidates(state["trend_candidates"])
    state["next_action"] = "score_trends"

    return state


def score_trends_node(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    트렌드 후보 점수 계산 (mention, embedding, recency 등)
    """
    repository.update_analysis_topic_status(
        state["topic_id"],
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


def rerank_trends_node(state):
    """
    LLM 기반 재정렬 (선택 단계)
    """
    repository.update_analysis_topic_status(
        state["topic_id"],
        TopicStatus.LLM_SUMMARIZING,
        "rerank_trends"
    )

    state["scored_trends"] = rerank_trends(
        state.get("scored_trends", []),
        state["topic"]
    )

    state["next_action"] = "generate_llm_summary"
    return state


def generate_llm_summary_node(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    LLM 기반 트렌드 요약 생성 (batch)
    """
    repository.update_analysis_topic_status(
        state["topic_id"],
        TopicStatus.LLM_SUMMARIZING,  
        "generate_llm_summary"
    )

    state["summarized_trends"] = generate_trend_summaries_batch(
        state.get("scored_trends", []),
        state.get("topic")
    )

    state["next_action"] = "select_representative_links"
    return state


def enrich_llm_output_node(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    LLM 결과와 기존 scoring 결과 merge (최종 정리 단계)
    """
    repository.update_analysis_topic_status(
        state.get("topic_id"),
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


def select_representative_links_node(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    각 트렌드별 대표 문서 링크 선정
    """
    trends = state.get("final_trends") or state.get("summarized_trends") or state.get("scored_trends", [])

    repository.update_analysis_topic_status(
        state.get("topic_id"),
        TopicStatus.SAVING,
        "select_representative_links"
    )

    state["final_trends"] = select_representative_links(trends)
    state["next_action"] = "save_result"
    return state


def save_result_node(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    최종 결과 DB 저장
    """
    repository.update_analysis_topic_status(
        state.get("topic_id"),
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


def return_result(state: TrendAnalysisState) -> TrendAnalysisState:
    """
    workflow 완료 처리 + 상태 업데이트
    """
    repository.update_analysis_topic_status(
        state["topic_id"],
        TopicStatus.COMPLETED,  
        "return_result",
        document_count=len(state.get("cleaned_documents", [])),
        trend_count=len(state.get("final_trends", [])),
    )

    return state


def clean_documents_from_dicts(documents: list[dict]) -> list[dict]:
    """
    dict → Document 변환 후 cleaner로 전달하는 adapter 함수
    """
    return clean_documents(
        [Document(**d) for d in documents]
    )
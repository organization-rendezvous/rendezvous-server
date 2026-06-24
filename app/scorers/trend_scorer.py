from __future__ import annotations
from datetime import datetime, UTC
from app.models.document import TrendDocument, TrendCandidate, TrendScores
from app.embeddings.similarity import cosine_similarity


INFLUENCE_BY_SOURCE = {
    "official": 100,
    "official_blog": 100,
    "rss": 65,
    "news": 80,
    "blog": 50,
    "community": 55,
}


# Time series

def _build_time_series(documents: list[TrendDocument]) -> list[dict]:
    buckets: dict[int, int] = {}

    now = datetime.now(UTC)

    for doc in documents:
        published = doc.published_at
        if not isinstance(published, datetime):
            continue

        if published.tzinfo is None:
            published = published.replace(tzinfo=UTC)

        hours_ago = int((now - published).total_seconds() // 3600)
        bucket = hours_ago // 6

        buckets[bucket] = buckets.get(bucket, 0) + 1

    return [{"bucket": k, "count": v} for k, v in sorted(buckets.items())]


def _trend_momentum_score(time_series: list[dict]) -> float:
    if not time_series:
        return 0.0

    if len(time_series) < 2:
        return 50.0

    series = sorted(time_series, key=lambda x: x["bucket"])

    growth_sum = 0.0
    steps = 0

    for i in range(1, len(series)):
        prev = series[i - 1]["count"]
        curr = series[i]["count"]

        if prev == 0:
            continue

        growth_sum += (curr - prev) / prev
        steps += 1

    if steps == 0:
        return 50.0

    avg_growth = growth_sum / steps
    return max(0.0, min(100.0, 50 + avg_growth * 50))


# Core scoring helpers

def _diversity_score(source_types: list[str]) -> float:
    return min(100.0, 35.0 + len(set(source_types)) * 22.0)


def _influence_score(source_types: list[str]) -> float:
    values = [INFLUENCE_BY_SOURCE.get(s, 45) for s in source_types]
    return sum(values) / len(values) if values else 0.0


def _recency_score(documents: list[TrendDocument]) -> float:
    published: list[datetime] = []

    for d in documents:
        if not isinstance(d.published_at, datetime):
            continue

        p = d.published_at
        if p.tzinfo is None:
            p = p.replace(tzinfo=UTC)

        published.append(p)

    if not published:
        return 25.0

    latest = max(published)

    age_hours = (datetime.now(UTC) - latest).total_seconds() / 3600

    if age_hours <= 1:
        return 100
    if age_hours <= 6:
        return 90
    if age_hours <= 24:
        return 75
    if age_hours <= 72:
        return 50
    if age_hours <= 168:
        return 25
    return 10


def _ai_importance_score(keywords: list[str]) -> float:
    important_terms = {
        "AI", "에이전트", "LLM", "보안",
        "자동화", "코딩", "개발자", "클라우드"
    }

    hits = sum(
        1 for k in keywords
        if any(term.lower() in k.lower() for term in important_terms)
    )

    return min(100.0, 65.0 + hits * 8.0)





def _embedding_score(
    trend_embedding: list[float] | None,
    document_embeddings: list[list[float]]
) -> float:
    if not trend_embedding:
        return 0.0

    if not document_embeddings:
        return 0.0

    similarities = [
        cosine_similarity(trend_embedding, emb)
        for emb in document_embeddings
        if emb
    ]

    if not similarities:
        return 0.0

    return sum(similarities) / len(similarities) * 100


# ----------------------------
# Main scoring function
# ----------------------------

def score_trends(candidates: list[TrendCandidate], result_limit: int) -> list[TrendCandidate]:
    if not candidates:
        return []

    max_mentions = max((c.mention_count for c in candidates), default=1)

    scored: list[TrendCandidate] = []

    for candidate in candidates:
        docs = candidate.documents

        time_series = _build_time_series(docs)

        scores = TrendScores(
            mention_score=candidate.mention_count / max_mentions * 100,
            diversity_score=_diversity_score(candidate.source_types),
            influence_score=_influence_score(candidate.source_types),
            recency_score=_recency_score(docs),
            ai_importance_score=_ai_importance_score(candidate.keywords),
           embedding_score=_embedding_score(candidate.embedding,
                                                [d.embedding 
                                                    for d in candidate.documents 
                                                        if d.embedding
                                                ]
                                            ),
            trend_momentum_score=_trend_momentum_score(time_series),
            final_score=0.0,  # 아래에서 계산
        )

        scores.final_score = (
            scores.mention_score * 0.18 +
            scores.diversity_score * 0.12 +
            scores.influence_score * 0.12 +
            scores.recency_score * 0.12 +
            scores.ai_importance_score * 0.12 +
            scores.embedding_score * 0.18 +
            scores.trend_momentum_score * 0.16
        )

        candidate.scores = scores
        candidate.time_series = time_series

        scored.append(candidate)

    return sorted(scored, key=lambda x: (x.scores.final_score if x.scores is not None else 0.0), reverse=True)[:result_limit]
import re
from collections import Counter

from app.analyzers.embedding_cluster import cluster_by_embedding
from app.models.document import TrendDocument, TrendCandidate
from app.embeddings.client import embed_texts


def generate_candidates(cleaned_documents: list[dict]) -> list[TrendCandidate]:
    """embedding 기반 clustering으로 candidate 생성 (typed version)"""

    documents = [
        {**doc, "embedding": doc.get("embedding")}
        for doc in cleaned_documents
    ]

    if any(doc["embedding"] is None for doc in documents):

        texts = [
            " ".join([
                doc.get("title", ""),
                doc.get("summary", ""),
                doc.get("raw_text", ""),
            ])
            for doc in documents
        ]

        embeddings = embed_texts(texts)
        documents = [
            {**doc, "embedding": embedding}
            for doc, embedding in zip(documents, embeddings)
        ]

    clusters = cluster_by_embedding(documents)
   
    candidates: list[TrendCandidate] = []

    for cluster in clusters:
        if not cluster:
            continue

        # 대표 title 선택
        title = ""
        for doc in cluster:
            t = doc.get("title", "").strip()
            if t:
                title = t
                break

        if not title:
            continue

        keywords = _extract_top_keywords(cluster)

        candidates.append(
            TrendCandidate(
                title=title,
                mention_count=len(cluster),
                source_types=list({d.get("source_type", "unknown") for d in cluster}),
                keywords=keywords,
                embedding=cluster[0].get("embedding"),
                documents=[
                   TrendDocument(
                        title=d.get("title", ""),
                        url=d.get("url", ""),
                        source_type=d.get("source_type", "unknown"),
                        published_at=d.get("published_at"),
                        summary=d.get("summary", ""),
                        embedding=d.get("embedding"),
                    )
                    for d in cluster
                ],
            )
        )

    return candidates


def _extract_top_keywords(cluster: list[dict]) -> list[str]:
    text = " ".join(
        (d.get("title", "") + " " + d.get("summary", ""))
        for d in cluster
    )

    words = re.findall(r"[A-Za-z가-힣]{2,}", text.lower())
    counter = Counter(words)

    return [w for w, _ in counter.most_common(8)]
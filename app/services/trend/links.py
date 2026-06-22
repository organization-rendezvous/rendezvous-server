from app.embeddings.similarity import cosine_similarity


SOURCE_CREDIBILITY = {
    "official": 100,
    "official_blog": 100,
    "news": 82,
    "rss": 70,
    "blog": 55,
}

def _embedding_similarity_score(trend_embedding, doc_embedding) -> float:
    if not trend_embedding or not doc_embedding:
        return 0.0
    return cosine_similarity(trend_embedding, doc_embedding) * 100


def _text_similarity_score(trend_title: str, doc_title: str) -> float:
    t = set(trend_title.lower().split())
    d = set(doc_title.lower().split())
    return min(100.0, len(t & d) * 15.0)


def select_representative_links(trends: list[dict], minimum: int = 3) -> list[dict]:
    enriched = []

    for trend in trends:
        docs = trend.get("documents", [])

        trend_embedding = trend.get("embedding")
        trend_title = trend.get("title", "")

        scored_docs = []

        for doc in docs:
            # Convert TrendDocument dataclass to dict if needed
            doc_dict = dict(doc.items()) if hasattr(doc, 'items') else doc
            
            source_type = doc_dict.get("source_type", "")
            cred = SOURCE_CREDIBILITY.get(source_type, 45)

            emb_score = _embedding_similarity_score(
                trend_embedding,
                doc_dict.get("embedding")
            )

            text_score = _text_similarity_score(
                trend_title,
                doc_dict.get("title", "")
            )

            final_score = (
                cred * 0.40 +
                emb_score * 0.35 +
                text_score * 0.25
            )

            scored_docs.append({
                **doc_dict,
                "source_name": doc_dict.get("source_name", "Unknown"),
                "credibility_score": cred,
                "embedding_score": emb_score,
                "text_similarity_score": text_score,
                "final_link_score": final_score,
            })

        ranked = sorted(
            scored_docs,
            key=lambda x: x["final_link_score"],
            reverse=True
        )

        enriched.append({
            **trend,
            "links": ranked[:minimum],
            "normalized_title": trend.get("normalized_title", trend.get("title", "").strip().lower())
        })

    return enriched
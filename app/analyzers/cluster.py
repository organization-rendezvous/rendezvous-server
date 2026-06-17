#클러스터 (몇게로 묶을지)를 정하지 않아도 되어서 KMeans을 사용하지 않음
from typing import List, Dict
from app.embeddings.similarity import cosine_similarity


def cluster_candidates(
    candidates: List[Dict],
    threshold: float = 0.82
) -> List[Dict]:

    clusters: List[Dict] = []

    for candidate in candidates:
        emb = candidate.get("embedding")
        if not emb:
            continue

        matched = False

        for cluster in clusters:
            similarity = cosine_similarity(emb, cluster["centroid"])

            if similarity >= threshold:
                cluster["items"].append(candidate)
                cluster["embeddings"].append(emb)

                cluster["centroid"] = _mean_vector(cluster["embeddings"])
                matched = True
                break

        if not matched:
            clusters.append({
                "centroid": emb,
                "embeddings": [emb],
                "items": [candidate],
            })

    return [
        {
            "title": c["items"][0]["title"],
            "documents": _merge_docs(c["items"]),
            "keywords": _merge_keywords(c["items"]),
            "source_types": _merge_sources(c["items"]),
            "mention_count": sum(i["mention_count"] for i in c["items"]),
        }
        for c in clusters
    ]


def _mean_vector(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []

    dim = len(vectors[0])
    return [
        sum(v[i] for v in vectors) / len(vectors)
        for i in range(dim)
    ]


def _merge_docs(items: list[dict]) -> list[dict]:
    docs = []
    for i in items:
        docs.extend(i.get("documents", []))
    return docs


def _merge_keywords(items: list[dict]) -> list[str]:
    keywords = []
    for i in items:
        keywords.extend(i.get("keywords", []))
    return list(set(keywords))[:10]


def _merge_sources(items: list[dict]) -> list[str]:
    sources = []
    for i in items:
        sources.extend(i.get("source_types", []))
    return list(set(sources))
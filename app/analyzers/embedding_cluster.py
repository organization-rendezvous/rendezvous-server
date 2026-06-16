from app.embeddings.similarity import cosine_similarity


def cluster_by_embedding(candidates: list[dict], threshold: float = 0.78) -> list[list[dict]]:
    clusters: list[list[dict]] = []

    for item in candidates:
        emb = item.get("embedding")
        if not emb:
            continue

        placed = False

        for cluster in clusters:
            centroid = _compute_centroid(cluster)

            if cosine_similarity(centroid, emb) >= threshold:
                cluster.append(item)
                placed = True
                break

        if not placed:
            clusters.append([item])

    return clusters


def _compute_centroid(cluster: list[dict]) -> list[float]:
    embeddings = [c["embedding"] for c in cluster if c.get("embedding")]

    if not embeddings:
        return []

    return [sum(x) / len(x) for x in zip(*embeddings)]
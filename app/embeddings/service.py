from app.embeddings.client import embed_texts
from app.embeddings.cache import batch_cache_lookup, set_cached_embedding


def get_embeddings(texts: list[str]) -> list[list[float]]:
    cached, missing = batch_cache_lookup(texts)

    results = []

    # 1. cached 먼저
    for t in texts:
        if t in cached:
            results.append(cached[t])

    # 2. missing batch embedding
    if missing:
        vectors = embed_texts(missing)

        for text, vec in zip(missing, vectors):
            set_cached_embedding(text, vec)

        results.extend(vectors)

    return results
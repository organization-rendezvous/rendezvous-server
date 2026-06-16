from openai import OpenAI
import os
from typing import cast
from app.embeddings.cache import embedding_cache

MODEL = "text-embedding-3-small"


def _get_openai_client():
    try:
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        return None


client = _get_openai_client()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    batch embedding + cache 적용
    """

    results: list[list[float] | None] = [None] * len(texts)
    to_request = []
    to_request_idx = []

    # 1. cache check
    for i, text in enumerate(texts):
        cached = embedding_cache.get(text)

        if cached is not None:
            results[i] = cached
        else:
            to_request.append(text)
            to_request_idx.append(i)

    # 2. API call only for missing
    if to_request:
        if client is None:
            # fallback for test or local environment
            import hashlib

            for idx, text in zip(to_request_idx, to_request):
                digest = hashlib.sha256(text.encode("utf-8")).digest()
                emb = [float(b) / 255.0 for b in digest[:64]]
                embedding_cache.set(text, emb)
                results[idx] = emb
        else:
            response = client.embeddings.create(
                model=MODEL,
                input=to_request
            )

            for idx, emb in zip(to_request_idx, response.data):
                embedding_cache.set(texts[idx], emb.embedding)
                results[idx] = emb.embedding

    # ensure no None remains
    if any(r is None for r in results):
        raise RuntimeError("Failed to produce all embeddings")

    return cast(list[list[float]], results)
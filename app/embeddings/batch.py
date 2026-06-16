from openai import OpenAI
import os
from typing import cast
from app.embeddings.cache import embedding_cache


def _get_openai_client():
    try:
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        return None

client = _get_openai_client()


def embed_batch(texts: list[str]) -> list[list[float]]:
    cached, missing_idx = embedding_cache.get_many(texts)

    if not missing_idx:
        # type: ignore - narrow to concrete type after runtime check
        return cast(list[list[float]], cached)

    to_embed = [texts[i] for i in missing_idx]

    if client is None:
        raise RuntimeError("OpenAI client is unavailable: make sure OPENAI_API_KEY is set")

    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=to_embed
    )

    embeddings = [d.embedding for d in res.data]

    for idx, emb in zip(missing_idx, embeddings):
        embedding_cache.set(texts[idx], emb)
        cached[idx] = emb

    return cast(list[list[float]], cached)
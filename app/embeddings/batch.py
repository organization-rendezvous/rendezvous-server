from app.llm.client import get_openai_client
from typing import cast
from app.embeddings.cache import embedding_cache

_client = get_openai_client()  # 모듈 로드 시점 1회 생성 


def embed_batch(texts: list[str]) -> list[list[float]]:
    cached, missing_idx = embedding_cache.get_many(texts)

    if not missing_idx:
        return cast(list[list[float]], cached)

    if _client is None:
        raise RuntimeError("OpenAI client is unavailable: make sure OPENAI_API_KEY is set")

    to_embed = [texts[i] for i in missing_idx]

    res = _client.embeddings.create(
        model="text-embedding-3-small",
        input=to_embed
    )

    embeddings = [d.embedding for d in res.data]

    for idx, emb in zip(missing_idx, embeddings):
        embedding_cache.set(texts[idx], emb)
        cached[idx] = emb

    return cast(list[list[float]], cached)
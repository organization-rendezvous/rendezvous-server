from app.llm.client import get_openai_client
from typing import cast
from app.embeddings.cache import embedding_cache
from app.core.config import get_settings

_client = get_openai_client()
_model = get_settings().openai_embedding_model  


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    batch embedding + cache 적용
    """
    results: list[list[float] | None] = [None] * len(texts)
    to_request = []
    to_request_idx = []

    for i, text in enumerate(texts):
        cached = embedding_cache.get(text)

        if cached is not None:
            results[i] = cached
        else:
            to_request.append(text)
            to_request_idx.append(i)

    if to_request:
        if _client is None:
            import hashlib

            for idx, text in zip(to_request_idx, to_request):
                digest = hashlib.sha256(text.encode("utf-8")).digest()
                emb = [float(b) / 255.0 for b in digest[:64]]
                embedding_cache.set(text, emb)
                results[idx] = emb
        else:
            response = _client.embeddings.create(
                model=_model,
                input=to_request
            )

            for idx, emb in zip(to_request_idx, response.data):
                embedding_cache.set(texts[idx], emb.embedding)
                results[idx] = emb.embedding

    if any(r is None for r in results):
        raise RuntimeError("Failed to produce all embeddings")

    return cast(list[list[float]], results)
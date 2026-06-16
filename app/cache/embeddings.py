import hashlib
from functools import lru_cache

from app.analyzers.embed_model import get_embedding_model


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

@lru_cache(maxsize=2048)
def get_cached_embedding(text: str) -> list[float]:
    model = get_embedding_model()
    vec = model.encode(text)
    return vec.tolist()


def embed_documents(texts: list[str]) -> list[list[float]]:
    return [get_cached_embedding(t) for t in texts]
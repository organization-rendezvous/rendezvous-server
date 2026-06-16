from collections import OrderedDict
import hashlib


MAX_CACHE_SIZE = 5000


class LRUEmbeddingCache:
    def __init__(self, max_size: int = MAX_CACHE_SIZE):
        self.max_size = max_size
        self.cache = OrderedDict()

    def _make_key(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def get(self, text: str):
        key = self._make_key(text)

        if key not in self.cache:
            return None

        self.cache.move_to_end(key)
        return self.cache[key]

    def get_many(self, texts: list[str]) -> tuple[list[list[float] | None], list[int]]:
        """Return list of embeddings or None for each text, and list of missing indices."""
        results: list[list[float] | None] = [None] * len(texts)
        missing: list[int] = []

        for i, t in enumerate(texts):
            v = self.get(t)
            if v is None:
                missing.append(i)
            results[i] = v

        return results, missing

    def set(self, text: str, embedding: list[float]):
        key = self._make_key(text)

        self.cache[key] = embedding
        self.cache.move_to_end(key)

        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)


embedding_cache = LRUEmbeddingCache()


def batch_cache_lookup(texts: list[str]) -> tuple[dict[str, list[float]], list[str]]:
    """Return cached mapping and list of missing texts."""
    cached: dict[str, list[float]] = {}
    missing: list[str] = []

    for t in texts:
        v = embedding_cache.get(t)
        if v is None:
            missing.append(t)
        else:
            cached[t] = v

    return cached, missing


def set_cached_embedding(text: str, emb: list[float]) -> None:
    embedding_cache.set(text, emb)
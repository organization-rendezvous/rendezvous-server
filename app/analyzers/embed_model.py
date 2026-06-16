from functools import lru_cache
from sentence_transformers import SentenceTransformer


@lru_cache
def get_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")
_llm_cache = {}

def get(key):
    return _llm_cache.get(key)

def set(key, value):
    _llm_cache[key] = value
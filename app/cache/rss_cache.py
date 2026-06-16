import time

_cache = {}
_TTL = 60 * 10  # 10분


def get_cache(key: str):
    item = _cache.get(key)
    if not item:
        return None

    value, ts = item
    if time.time() - ts > _TTL:
        del _cache[key]
        return None

    return value


def set_cache(key: str, value):
    _cache[key] = (value, time.time())
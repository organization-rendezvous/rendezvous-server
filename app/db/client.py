from functools import lru_cache
from typing import Any

from app.core.config import get_settings


@lru_cache
def get_supabase_client() -> Any | None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None

    try:
        import importlib
        supabase = importlib.import_module("supabase")
        create_client = getattr(supabase, "create_client")
    except Exception:
        return None

    return create_client(settings.supabase_url, settings.supabase_service_role_key)

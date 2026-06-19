
from __future__ import annotations
from datetime import UTC, datetime

from app.db.repositories.supabase import SupabaseRepository
from app.db.repositories.inmemory.inmemory_repositorie import InMemoryRepository

repository = SupabaseRepository()
# repository = InMemoryRepository() import UTC, datetime
# 테스트 용도
from app.db.repositories.inmemory.inmemory_repositorie import InMemoryRepository
# supabase 레포지토리
from app.db.repositories.supabase import SupabaseRepository

# 환경변수
from app.core.config import get_settings
settings = get_settings()

def utc_now() -> datetime:
    return datetime.now(UTC)

if settings.supabase_url and settings.supabase_service_role_key:
    repository = SupabaseRepository()
else:
    repository = InMemoryRepository()
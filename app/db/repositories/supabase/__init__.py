from __future__ import annotations
from app.db.client import get_supabase_client

from .jobs import JobsMixin
from .topics import TopicsMixin
from .trends import TrendsMixin
from .settings import SettingsMixin


class SupabaseRepository(JobsMixin, TopicsMixin, TrendsMixin, SettingsMixin):
    def __init__(self):
        self.client = get_supabase_client()


__all__ = ["SupabaseRepository"]
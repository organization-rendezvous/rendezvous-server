from __future__ import annotations
from app.schemas.settings import UserSettingsResponse


class SettingsMixin:
    """user_settings 테이블 관련 메서드."""

    def get_user_settings(self, user_id: str) -> dict:
        res = (
            self.client.table("user_settings")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if not res.data:
            default = UserSettingsResponse(user_id=user_id).model_dump()
            return self.upsert_user_settings(default)
        return res.data

    def upsert_user_settings(self, settings: dict) -> dict:
        res = (
            self.client.table("user_settings")
            .upsert(settings, on_conflict="user_id")
            .execute()
        )
        return res.data[0]
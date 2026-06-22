from app.db.repository_factory import repository


class MdSettingsService:
    def __init__(self):
        self.repository = repository

    def get_settings(self, user_id: str) -> dict:
        res = (
            self.repository.client.table("user_md_settings")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )

        if not res.data:
            return self._default_settings(user_id)

        return res.data or self._default_settings(user_id)
        
    def upsert(self, user_id: str, payload: dict) -> dict:
        row = {
            "user_id": user_id,

            "enabled_topics": payload.get("enabled_topics", []),
            "section_order": payload.get("section_order", []),

            "result_limit": payload.get("result_limit", 5),

            "include_summary": payload.get("include_summary", True),
            "include_detail_summary": payload.get("include_detail_summary", True),
            "include_keywords": payload.get("include_keywords", True),
            "include_links": payload.get("include_links", True),

            "file_name_pattern": payload.get("file_name_pattern", "daily-briefing-{date}"),
            "timezone": payload.get("timezone", "Asia/Seoul"),

            "save_path": payload.get("save_path"),
        }

        res = (
            self.repository.client
            .table("user_md_settings")
            .upsert(row, on_conflict="user_id")
            .execute()
        )

        return res.data[0]

    def _default_settings(self, user_id: str) -> dict:
        return {
            "user_id": user_id,
            "enabled_topics": ["개발", "AI", "사회"],
            "result_limit": 5,
            "include_links": True,
            "section_order": ["개발", "AI", "사회"],
            "include_summary": True,
            "include_detail_summary": True,
            "include_keywords": True,
            "file_name_pattern": "daily-briefing-{date}",
            "timezone": "Asia/Seoul",
        }
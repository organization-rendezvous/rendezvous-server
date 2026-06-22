from pydantic import BaseModel

class MdSettingsPayload(BaseModel):
    enabled_topics: list[str]
    section_order: list[str] = []
    result_limit: int = 5

    include_summary: bool = True
    include_detail_summary: bool = True
    include_keywords: bool = True
    include_links: bool = True

    file_name_pattern: str = "daily-briefing-{date}"
    timezone: str = "Asia/Seoul"

    save_path: str | None = None
from pydantic import BaseModel, Field
from app.core.config import get_settings

settings = get_settings()


class UserSettingsResponse(BaseModel):
    user_id: str = "personal-user"
    enabled_topics: list[str] = Field(default_factory=lambda: settings.default_topics)
    custom_topics: list[str] = Field(default_factory=list)
    period: str = "24h"
    result_limit: int = 5
    enabled_sources: list[str] = Field(default_factory=lambda: settings.default_sources)


class UpdateUserSettingsRequest(UserSettingsResponse):
    pass
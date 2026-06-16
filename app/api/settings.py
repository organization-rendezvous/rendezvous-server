from fastapi import APIRouter

from app.db.repositories import repository
from app.schemas.settings import UpdateUserSettingsRequest, UserSettingsResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_settings(user_id: str = "personal-user") -> UserSettingsResponse:
    return UserSettingsResponse(**repository.get_user_settings(user_id))


@router.put("")
async def update_settings(request: UpdateUserSettingsRequest) -> UserSettingsResponse:
    return UserSettingsResponse(**repository.upsert_user_settings(request.model_dump()))

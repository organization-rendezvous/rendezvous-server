from datetime import datetime, timezone
from app.db.repository_factory import repository
from app.services.md.md_job_service import MdJobService


class MdJobResolver:
    def __init__(self):
        self.job_service = MdJobService()
        self.repository = repository

    async def resolve_today_job(self, user_id: str) -> dict:
        job = self._get_latest_today_job(user_id)

        if job:
            return job

        new_job = await self.job_service.run_analysis_job_for_md(user_id)
        return new_job

    def _get_latest_today_job(self, user_id: str) -> dict | None:
        today = datetime.now(timezone.utc).date().isoformat()

        res = (
            self.repository.client.table("analysis_jobs")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "completed")
            .gte("created_at", today + "T00:00:00Z")
            .lt("created_at", today + "T23:59:59Z")
            .order("completed_at", desc=True)
            .limit(1)
            .execute()
        )

        data = res.data or []
        return data[0] if data else None
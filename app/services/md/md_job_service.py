# app/services/md_job_service.py

from app.services.trend.analysis import run_analysis_job
from app.db.repository_factory import repository


class MdJobService:
    def __init__(self):
        self.repository = repository

    async def run_analysis_job_for_md(self, user_id: str) -> dict:
        """
        MD 생성을 위한 job 보장 + 실행 래퍼
        """

        job = self._get_latest_today_job(user_id)

        # 1. 오늘 job이 없으면 생성
        if not job:
            job = self._create_today_job(user_id)

        job_id = job["id"]

        # 2. 이미 완료된 job이면 재실행 안 함
        if job.get("status") == "completed":
            return job

        # 3. analysis 실행
        await run_analysis_job(job_id)

        # 4. 최신 상태 반환
        return self.repository.get_job_status(job_id)

    # -------------------------
    # 내부 유틸
    # -------------------------
    def _get_latest_today_job(self, user_id: str) -> dict | None:
        res = (
            self.repository.client.table("analysis_jobs")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def _create_today_job(self, user_id: str) -> dict:
        res = (
            self.repository.client.table("analysis_jobs")
            .insert({
                "user_id": user_id,
                "status": "pending",
                "period": "24h",
                "result_limit": 5,
                "sources": [],
            })
            .execute()
        )
        return res.data[0]
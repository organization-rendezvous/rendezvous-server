import os
from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.services.md.md_export_service import MdExportService
from app.services.md.md_settings_service import MdSettingsService
from app.db.repository_factory import repository
from app.schemas.md import MdSettingsPayload

router = APIRouter(prefix="/md", tags=["md"])


@router.post("/export")
async def export_md(user_id: str = "personal-user"):
    service = MdExportService()
    result = await service.export(user_id)
    return result


@router.get("/download/{file_name}")
def download_md(file_name: str, user_id: str = "personal-user"):
    
    service = MdSettingsService()
    settings = service.get_settings(user_id)

    save_path = os.path.expanduser(settings.get("save_path", "./exports"))
    file_path = os.path.join(save_path, file_name)

    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

    return FileResponse(file_path, media_type="text/markdown")


@router.get("/jobs/{job_id}/status")
def get_job_status(job_id: str):
    status = repository.get_job_status(job_id)

    job = status["job"]
    topics = status["topics"]

    return {
        "job_id": job_id,
        "status": job["status"],
        "topics": [
            {
                "id": t["id"],
                "name": t["topic_name"],
                "status": t["status"],
                "current_step": t.get("current_step"),
                "document_count": t.get("document_count", 0),
                "trend_count": t.get("trend_count", 0),
            }
            for t in topics
        ],
    }


@router.get("/jobs/{job_id}/progress")
def get_job_progress(job_id: str):
    status = repository.get_job_status(job_id)
    topics = status["topics"]

    total = len(topics)
    if total == 0:
        return {
            "progress": 0,
            "status": status["job"]["status"]
        }

    completed = len([
        t for t in topics
        if t["status"] == "completed"
    ])

    failed = len([
        t for t in topics
        if t["status"] == "failed"
    ])

    running = len([
        t for t in topics
        if t["status"] == "running"
    ])

    progress = int((completed / total) * 100)

    return {
        "job_id": job_id,
        "progress": progress,
        "completed": completed,
        "running": running,
        "failed": failed,
        "total": total,
        "status": status["job"]["status"],
    }



@router.get("/{user_id}")
def get_settings(user_id: str):
    service = MdSettingsService()
    return service.get_settings(user_id)


@router.post("/{user_id}")
def update_settings(user_id: str, payload: MdSettingsPayload):
    service = MdSettingsService()
    return service.upsert(user_id, payload.model_dump())
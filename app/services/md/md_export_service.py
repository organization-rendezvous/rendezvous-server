from app.db.repository_factory import repository
from app.services.md.md_job_resolver import MdJobResolver
from app.services.md.md_settings_service import MdSettingsService
from app.services.md.md_data_loader import MdDataLoader
from app.services.md.md_renderer import MdRenderer
from app.services.md.md_exporter import MdExporter


class MdExportService:
    def __init__(self):
        self.repository = repository
        self.job_resolver = MdJobResolver()
        self.settings_service = MdSettingsService()
        self.loader = MdDataLoader(repository)
        self.renderer = MdRenderer()
        self.exporter = MdExporter()

    async def export(self, user_id: str) -> dict:
        job = await self.job_resolver.resolve_today_job(user_id)

        settings = self.settings_service.get_settings(user_id)

        data = self.loader.load(job["id"])

        md = self.renderer.render(data, settings)

        file_path, file_name = self.exporter.write(md, settings)

        return {
            "file_name": file_name,
            "file_path": file_path,
            "download_url": f"/md/download/{file_name}",
        }
    

    def _file_name(self) -> str:
        from datetime import datetime, timezone

        today = datetime.now(timezone.utc).date().isoformat()
        return f"daily-briefing-{today}.md"
        
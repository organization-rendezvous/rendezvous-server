import os
from datetime import datetime, timezone

class MdExporter:

    def write(self, content: str, settings: dict) -> tuple[str, str]:
        save_path = os.path.expanduser(settings.get("save_path", "./exports"))

        os.makedirs(save_path, exist_ok=True)

        file_name = self._file_name()
        file_path = os.path.join(save_path, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return file_path, file_name

    def _file_name(self):
        today = datetime.now(timezone.utc).date().isoformat()
        return f"daily-briefing-{today}.md"
from app.core.config import STEP_PROGRESS_MAP
from app.core.types import PipelineStep


def get_progress(step: PipelineStep | None) -> int:
    if not step:
        return 0
    return STEP_PROGRESS_MAP.get(step, 0)
from enum import Enum

#내부에서 사용하는 타입
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL_FAILED = "partial_failed"
    FAILED = "failed"


class PipelineStep(str, Enum):
    COLLECTING = "collecting"
    CLEANING = "cleaning"
    CLUSTERING = "clustering"
    EMBEDDING = "embedding"
    SCORING = "scoring"
    LLM_SUMMARIZING = "llm_summarizing"
    SAVING = "saving"


class TopicStatus(str, Enum):
    PENDING = "pending"
    COLLECTING = "collecting"
    CLEANING = "cleaning"
    CLUSTERING = "clustering"
    SCORING = "scoring"
    LLM_SUMMARIZING = "llm_summarizing"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def progress_weight(self) -> int:
        return {
            TopicStatus.PENDING: 0,
            TopicStatus.COLLECTING: 15,
            TopicStatus.CLEANING: 30,
            TopicStatus.CLUSTERING: 45,
            TopicStatus.SCORING: 60,
            TopicStatus.LLM_SUMMARIZING: 75,
            TopicStatus.SAVING: 90,
            TopicStatus.COMPLETED: 100,
            TopicStatus.FAILED: 100,
        }[self]
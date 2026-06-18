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
    EMBEDDING = "embedding"     
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
            TopicStatus.EMBEDDING: 60,     # ← 추가
            TopicStatus.SCORING: 70,       # ← 기존 60에서 조정
            TopicStatus.LLM_SUMMARIZING: 80,  # ← 기존 75에서 조정
            TopicStatus.SAVING: 90,
            TopicStatus.COMPLETED: 100,
            TopicStatus.FAILED: 100,
        }[self]